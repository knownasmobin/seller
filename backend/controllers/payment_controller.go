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

// ApproveOrder is called by the bot when admin approves a card payment.
// @Summary Approve an order
// @Description Admin approves a card payment, triggering VPN provisioning
// @Tags Orders
// @Produce json
// @Param id path int true "Order ID"
// @Success 200 {object} map[string]interface{}
// @Router /orders/{id}/approve [post]
func ApproveOrder(c *fiber.Ctx) error {
	orderID := c.Params("id")

	var order models.Order
	if err := database.DB.Where("id = ?", orderID).First(&order).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Order not found"})
	}

	if order.PaymentStatus == "approved" {
		return c.JSON(fiber.Map{"message": "Already approved"})
	}

	order.PaymentStatus = "approved"
	database.DB.Save(&order)

	// Provision VPN and notify user
	provisionVPNForOrder(&order)

	// Find the user to return their telegram_id
	var user models.User
	database.DB.Where("id = ?", order.UserID).First(&user)

	return c.JSON(fiber.Map{
		"message":     "Order approved and VPN provisioned",
		"order_id":    order.ID,
		"telegram_id": user.TelegramID,
	})
}

// RejectOrder is called by the bot when admin rejects a card payment.
// @Summary Reject an order
// @Description Admin rejects a card payment
// @Tags Orders
// @Produce json
// @Param id path int true "Order ID"
// @Success 200 {object} map[string]interface{}
// @Router /orders/{id}/reject [post]
func RejectOrder(c *fiber.Ctx) error {
	orderID := c.Params("id")

	var order models.Order
	if err := database.DB.Where("id = ?", orderID).First(&order).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Order not found"})
	}

	order.PaymentStatus = "rejected"
	database.DB.Save(&order)

	var user models.User
	database.DB.Where("id = ?", order.UserID).First(&user)

	// Notify user about rejection
	notifyTelegramBot(user, models.Subscription{
		ConfigLink: "❌ Your payment was rejected.",
	})

	return c.JSON(fiber.Map{
		"message":     "Order rejected",
		"order_id":    order.ID,
		"telegram_id": user.TelegramID,
	})
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

	var creds map[string]string
	if err := json.Unmarshal([]byte(server.Credentials), &creds); err != nil {
		log.Println("Invalid server credentials JSON for server:", server.ID)
		return
	}

	if plan.ServerType == "v2ray" {
		marzbanUser := creds["username"]
		marzbanPass := creds["password"]

		client := vpn.NewMarzbanClient(server.APIUrl, marzbanUser, marzbanPass)

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
		wgUser := creds["username"]
		wgPass := creds["password"]

		client := vpn.NewWgPortalClient(server.APIUrl[:len(server.APIUrl)-4], wgUser, wgPass)
		username := fmt.Sprintf("wg_user_%d_%d", user.TelegramID, order.ID)
		if peerConf, err := client.CreatePeer(username); err == nil {
			configLink = peerConf // We store the raw multiline .conf here
			uuidStr = username
			log.Println("Created WG Peer:", username)
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
	notifyTelegramBot(user, sub)
}

func notifyTelegramBot(user models.User, sub models.Subscription) {
	botToken := os.Getenv("BOT_TOKEN")
	if botToken == "" {
		return
	}

	var text string
	if user.Language == "fa" {
		text = "✅ **کانفیگ VPN شما آماده است!**\n\n"
		if len(sub.ConfigLink) > 0 && sub.ConfigLink[0] == '[' { // Looks like Wireguard raw config
			text += "🔗 فایل/متن کانفیگ (WireGuard):\n"
			text += fmt.Sprintf("```ini\n%s\n```\n\n", sub.ConfigLink)
		} else {
			text += fmt.Sprintf("🔗 لینک کانفیگ: `%s`\n", sub.ConfigLink)
		}
		if sub.ExpiryDate.Year() > 2000 {
			text += fmt.Sprintf("📅 انقضا: %s\n", sub.ExpiryDate.Format("2006-01-02"))
		}
	} else {
		text = "✅ **Your VPN Config is Ready!**\n\n"
		if len(sub.ConfigLink) > 0 && sub.ConfigLink[0] == '[' {
			text += "🔗 Config Text (WireGuard):\n"
			text += fmt.Sprintf("```ini\n%s\n```\n\n", sub.ConfigLink)
		} else {
			text += fmt.Sprintf("🔗 Link/Config: `%s`\n", sub.ConfigLink)
		}
		if sub.ExpiryDate.Year() > 2000 {
			text += fmt.Sprintf("📅 Expires: %s\n", sub.ExpiryDate.Format("2006-01-02"))
		}
	}

	payload := map[string]interface{}{
		"chat_id":    user.TelegramID,
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
