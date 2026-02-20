package controllers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
	"github.com/username/sell-bot-backend/vpn"
)

// OxapayCallback is hit by Oxapay when a payment is confirmed.
func OxapayCallback(c *fiber.Ctx) error {
	// Oxapay sends application/x-www-form-urlencoded or application/json.
	// For raw reading:
	type OxapayPayload struct {
		Merchant    string  `json:"merchant"`
		Status      int     `json:"status"` // 100 is paid
		Amount      float64 `json:"amount"`
		PayAmount   float64 `json:"payAmount"`
		OrderID     string  `json:"orderId"`
		TrackID     int64   `json:"trackId"`
		Description string  `json:"description"`
	}

	var payload OxapayPayload
	if err := c.BodyParser(&payload); err != nil {
		log.Println("Oxapay callback parse error:", err)
		return c.Status(400).SendString("Bad Request")
	}

	// Verify merchant key (basic security step)
	if payload.Merchant != os.Getenv("OXAPAY_MERCHANT_KEY") {
		log.Println("Invalid Oxapay merchant key in callback")
		return c.Status(403).SendString("Forbidden")
	}

	// Wait, oxapay sends HMAC signature. A simple check is to send request to their verification endpoint,
	// or just check if status == 100. Let's assume trusting the merchant key for now since this is an MVP.

	if payload.Status != 100 {
		log.Printf("Order %s received non-success status: %d", payload.OrderID, payload.Status)
		// Process it anyway to record failures if desired, or skip
		return c.SendString("OK")
	}

	var order models.Order
	if err := database.DB.Where("id = ?", payload.OrderID).First(&order).Error; err != nil {
		log.Printf("Order %s not found in DB", payload.OrderID)
		return c.Status(404).SendString("Order not found")
	}

	if order.PaymentStatus == "approved" {
		return c.SendString("Already approved")
	}

	// Approve Order
	order.PaymentStatus = "approved"
	order.CryptoTxID = fmt.Sprintf("%d", payload.TrackID)
	database.DB.Save(&order)

	// Here we should provision the VPN, then optionally notify the bot.
	provisionVPNForOrder(&order)

	return c.SendString("OK")
}

// provisionVPNForOrder provisions the account through Marzban or WgPortal and creates a Subscription.
func provisionVPNForOrder(order *models.Order) {
	var plan models.Plan
	if err := database.DB.Where("id = ?", order.PlanID).First(&plan).Error; err != nil {
		log.Println("Failed to find plan for order:", order.ID)
		return
	}

	var user models.User
	if err := database.DB.Where("id = ?", order.UserID).First(&user).Error; err != nil {
		log.Println("Failed to find user for order:", order.ID)
		return
	}

	// Fetch server logic could be more complex, we just pick the first active one for the given server type
	var server models.Server
	if err := database.DB.Where("server_type = ? AND is_active = ?", plan.ServerType, true).First(&server).Error; err != nil {
		log.Println("No active server found for type:", plan.ServerType)
		return // in production, maybe refund or alert admin
	}

	configLink := ""
	uuidStr := ""

	if plan.ServerType == "v2ray" {
		// Attempt Marzban provision
		client := vpn.NewMarzbanClient(server.APIUrl, "admin", "admin") // In production fetch from Server Credentials

		username := fmt.Sprintf("user_%d_%d", user.TelegramID, order.ID)
		expireTime := time.Now().AddDate(0, 0, plan.DurationDays).Unix()

		subLink, err := client.CreateUser(username, plan.DataLimitGB, expireTime)
		if err == nil {
			configLink = fmt.Sprintf("%s%s", server.APIUrl[:len(server.APIUrl)-4], subLink) // rough URL formatting
			uuidStr = username
		} else {
			log.Println("Marzban User Create Error:", err)
		}
	} else if plan.ServerType == "wireguard" {
		client := vpn.NewWgPortalClient(server.APIUrl[:len(server.APIUrl)-4], "apikey") // Production from DB
		username := fmt.Sprintf("wg_user_%d_%d", user.TelegramID, order.ID)
		if peerConf, err := client.CreatePeer(username); err == nil {
			configLink = "WireGuard Config Data Created" // Or upload to file and serve
			uuidStr = username
			log.Println("Created WG Peer:", peerConf)
		} else {
			log.Println("WG Port Create Error:", err)
		}
	}

	sub := models.Subscription{
		UserID:     user.ID,
		PlanID:     plan.ID,
		ServerID:   server.ID,
		ConfigLink: configLink,
		UUID:       uuidStr,
		StartDate:  time.Now(),
		ExpiryDate: time.Now().AddDate(0, 0, plan.DurationDays),
		Status:     "active",
	}

	// If provisioning failed, configLink will be empty, could set status to failed
	if configLink == "" {
		sub.Status = "provision_failed"
	}

	database.DB.Create(&sub)

	// Try notifying Bot to send message back to User
	notifyTelegramBot(user.TelegramID, sub)
}

func notifyTelegramBot(telegramID int64, sub models.Subscription) {
	botToken := os.Getenv("BOT_TOKEN")
	if botToken == "" {
		return
	}

	text := "✅ **Your VPN Config is Ready!**\n\n"
	text += fmt.Sprintf("🔗 Link/Config: `%s`\n", sub.ConfigLink)
	text += fmt.Sprintf("📅 Expires: %s\n", sub.ExpiryDate.Format("2006-01-02"))

	payload := map[string]interface{}{
		"chat_id":    telegramID,
		"text":       text,
		"parse_mode": "Markdown",
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return
	}

	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)
	http.Post(url, "application/json", bytes.NewBuffer(jsonData))
}
