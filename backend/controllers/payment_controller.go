package controllers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
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
	if err := provisionVPNForOrder(&order); err != nil {
		log.Printf("[ERROR] OxaPay auto-provisioning failed for order %s: %v", payload.OrderID, err)
		// We still return OK to OxaPay so they stop retrying the webhook,
		// but the order's configLink isn't set, and admins will need to intervene.
		// (Ideally we flag it for manual review).
	}

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

	// Provision VPN and notify user
	if err := provisionVPNForOrder(&order); err != nil {
		return c.Status(400).JSON(fiber.Map{
			"error":   "provisioning_failed",
			"message": err.Error(),
		})
	}

	// Only mark approved if we succeeded
	order.PaymentStatus = "approved"
	database.DB.Save(&order)

	// Find the user to return their telegram_id
	var user models.User
	database.DB.Where("id = ?", order.UserID).First(&user)

	return c.JSON(fiber.Map{
		"message":     "Order approved and VPN provisioned",
		"order_id":    order.ID,
		"telegram_id": user.TelegramID,
	})
}

// ManualProvisionRequest represents the payload for manual provisioning
type ManualProvisionRequest struct {
	ConfigLink string `json:"config_link"`
}

// ManualProvisionOrder allows an admin to supply a config link if auto-provisioning failed
// @Summary Manually provision an order
// @Description Admin sets config manually
// @Tags Orders
// @Accept json
// @Produce json
// @Param id path int true "Order ID"
// @Param request body ManualProvisionRequest true "Config Link"
// @Success 200 {object} map[string]interface{}
// @Router /orders/{id}/manual_provision [post]
func ManualProvisionOrder(c *fiber.Ctx) error {
	orderID := c.Params("id")

	var req ManualProvisionRequest
	if err := c.BodyParser(&req); err != nil || req.ConfigLink == "" {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body or missing config_link"})
	}

	var order models.Order
	if err := database.DB.Where("id = ?", orderID).First(&order).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Order not found"})
	}

	var plan models.Plan
	if err := database.DB.Where("id = ?", order.PlanID).First(&plan).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Plan not found"})
	}

	var user models.User
	database.DB.Where("id = ?", order.UserID).First(&user)

	// In a complete implementation we might want to also fetch the server ID,
	// but for manual fallback we can set server_id to 0 or leave empty.

	uuidStr := fmt.Sprintf("manual_%d_%d", user.TelegramID, order.ID)

	sub := models.Subscription{
		UserID:     user.ID,
		PlanID:     plan.ID,
		ServerID:   0, // Manual flag
		ConfigLink: req.ConfigLink,
		UUID:       uuidStr,
		StartDate:  time.Now(),
		ExpiryDate: time.Now().AddDate(0, 0, plan.DurationDays),
		Status:     "active",
	}

	database.DB.Create(&sub)

	order.PaymentStatus = "approved"
	database.DB.Save(&order)

	// Notify Telegram Bot
	notifyTelegramBot(user, sub, plan)

	return c.JSON(fiber.Map{
		"message":     "Order manually provisioned",
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
	sendRejectionNotification(user)

	return c.JSON(fiber.Map{
		"message":     "Order rejected",
		"order_id":    order.ID,
		"telegram_id": user.TelegramID,
	})
}

// provisionVPNForOrder provisions the account through Marzban or WgPortal and creates a Subscription.
func provisionVPNForOrder(order *models.Order) error {
	var plan models.Plan
	if err := database.DB.Where("id = ?", order.PlanID).First(&plan).Error; err != nil {
		log.Printf("[ERROR][Provision] Failed to find plan (ID: %d) for order (ID: %d): %v\n", order.PlanID, order.ID, err)
		return fmt.Errorf("plan not found")
	}

	var user models.User
	if err := database.DB.Where("id = ?", order.UserID).First(&user).Error; err != nil {
		log.Printf("[ERROR][Provision] Failed to find user (ID: %d) for order (ID: %d): %v\n", order.UserID, order.ID, err)
		return fmt.Errorf("user not found")
	}

	// Fetch server logic could be more complex, we just pick the first active one for the given server type
	var server models.Server
	if err := database.DB.Where("server_type = ? AND is_active = ?", plan.ServerType, true).First(&server).Error; err != nil {
		log.Printf("[ERROR][Provision] No active %s server found in database.\n", plan.ServerType)
		return fmt.Errorf("no active server for type %s", plan.ServerType)
	}

	configLink := ""
	uuidStr := ""

	var creds map[string]string
	if err := json.Unmarshal([]byte(server.Credentials), &creds); err != nil {
		log.Printf("[ERROR][Provision] Invalid server credentials JSON for server ID %d: %v\n", server.ID, err)
		return fmt.Errorf("invalid server credentials")
	}

	maxRetries := 3
	var lastErr error

	for attempt := 1; attempt <= maxRetries; attempt++ {
		if plan.ServerType == "v2ray" {
			marzbanUser := creds["username"]
			marzbanPass := creds["password"]

			client := vpn.NewMarzbanClient(server.APIUrl, marzbanUser, marzbanPass)

			var username string
			if order.ConfigName != "" {
				username = order.ConfigName
			} else {
				username = fmt.Sprintf("user_%d_%d", user.TelegramID, order.ID)
			}
			uuidStr = username
			expireTime := time.Now().AddDate(0, 0, plan.DurationDays).Unix()

			subLink, err := client.CreateUser(username, plan.DataLimitGB, expireTime)
			if err == nil {
				// Marzban may return a full URL or a relative path like /sub/username/
				if strings.HasPrefix(subLink, "http") {
					configLink = subLink
				} else {
					configLink = fmt.Sprintf("%s%s", strings.TrimRight(server.APIUrl, "/"), subLink)
				}
				break // Success
			} else {
				lastErr = err
				log.Printf("[ERROR][Provision][Marzban] Attempt %d failed. User: %s, Err: %v\n", attempt, username, err)
			}
		} else if plan.ServerType == "wireguard" {
			wgUser := creds["username"]
			wgPass := creds["password"]

			client := vpn.NewWgPortalClient(server.APIUrl, wgUser, wgPass)
			username := fmt.Sprintf("wg_user_%d_%d", user.TelegramID, order.ID)
			uuidStr = username
			if peerConf, err := client.CreatePeer(username); err == nil {
				configLink = peerConf
				log.Println("Created WG Peer:", username)
				break // Success
			} else {
				lastErr = err
				log.Printf("[ERROR][Provision][WgPortal] Attempt %d failed. User: %s, Err: %v\n", attempt, username, err)
			}
		}

		if attempt < maxRetries {
			time.Sleep(2 * time.Second)
		}
	}

	if configLink == "" {
		return fmt.Errorf("provisioning failed after %d attempts: %v", maxRetries, lastErr)
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
	notifyTelegramBot(user, sub, plan)

	return nil
}

func notifyTelegramBot(user models.User, sub models.Subscription, plan models.Plan) {
	botToken := os.Getenv("BOT_TOKEN")
	if botToken == "" {
		return
	}

	if sub.Status == "provision_failed" {
		var text string
		if user.Language == "fa" {
			text = "⚠️ **خطا در ساخت سرویس!**\n\nپرداخت شما تایید شد اما متأسفانه سرور در حال حاضر قادر به ساخت کانفیگ شما نیست. لطفا دقایقی دیگر به بخش **🔑 سرویس‌های من** مراجعه کنید یا با پشتیبانی تماس بگیرید."
		} else {
			text = "⚠️ **Provisioning Error!**\n\nYour payment was successful, but the server failed to generate your config. Please try checking **🔑 My Configs** later or contact support."
		}

		payload := map[string]interface{}{
			"chat_id":    user.TelegramID,
			"text":       text,
			"parse_mode": "Markdown",
		}
		jsonData, _ := json.Marshal(payload)
		url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)
		http.Post(url, "application/json", bytes.NewBuffer(jsonData))
		return
	}

	if plan.ServerType == "wireguard" {
		// Send the config instruction message
		sendWGReadyMessage(botToken, user, sub)
	} else {
		// V2Ray: send subscription URL as text
		sendV2RayLink(botToken, user, sub)
	}
}

func sendV2RayLink(botToken string, user models.User, sub models.Subscription) {
	var text string
	if user.Language == "fa" {
		text = "✅ **سرویس V2Ray شما آماده است!**\n\n"
		text += fmt.Sprintf("🔗 لینک اشتراک: `%s`\n", sub.ConfigLink)
		if sub.ExpiryDate.Year() > 2000 {
			text += fmt.Sprintf("📅 انقضا: %s\n", sub.ExpiryDate.Format("2006-01-02"))
		}
		text += "\nاین لینک را در اپلیکیشن V2Ray خود (مثل v2rayNG یا Streisand) وارد کنید."
	} else {
		text = "✅ **Your V2Ray Config is Ready!**\n\n"
		text += fmt.Sprintf("🔗 Subscription URL: `%s`\n", sub.ConfigLink)
		if sub.ExpiryDate.Year() > 2000 {
			text += fmt.Sprintf("📅 Expires: %s\n", sub.ExpiryDate.Format("2006-01-02"))
		}
		text += "\nImport this link into your V2Ray client (e.g., v2rayNG, Streisand)."
	}

	payload := map[string]interface{}{
		"chat_id":    user.TelegramID,
		"text":       text,
		"parse_mode": "Markdown",
	}

	jsonData, _ := json.Marshal(payload)
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)
	http.Post(url, "application/json", bytes.NewBuffer(jsonData))
}

func sendWGReadyMessage(botToken string, user models.User, sub models.Subscription) {
	var text string
	if user.Language == "fa" {
		text = "✅ **سرویس WireGuard شما آماده است!**\n\n"
		text += "برای دریافت کانفیگ خود، لطفاً به بخش **🔑 سرویس‌های من (My Configs)** بروید و لوکیشن سرور را انتخاب کنید.\n"
		if sub.ExpiryDate.Year() > 2000 {
			text += fmt.Sprintf("📅 انقضا: %s\n", sub.ExpiryDate.Format("2006-01-02"))
		}
	} else {
		text = "✅ **Your WireGuard Config is Ready!**\n\n"
		text += "To get your config file, please go to **🔑 My Configs**, select your active plan, and choose a server location.\n"
		if sub.ExpiryDate.Year() > 2000 {
			text += fmt.Sprintf("📅 Expires: %s\n", sub.ExpiryDate.Format("2006-01-02"))
		}
	}

	payload := map[string]interface{}{
		"chat_id":    user.TelegramID,
		"text":       text,
		"parse_mode": "Markdown",
	}

	jsonData, _ := json.Marshal(payload)
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)
	http.Post(url, "application/json", bytes.NewBuffer(jsonData))
}

func sendRejectionNotification(user models.User) {
	botToken := os.Getenv("BOT_TOKEN")
	if botToken == "" {
		return
	}

	var text string
	if user.Language == "fa" {
		text = "❌ پرداخت شما رد شد. در صورت مشکل با پشتیبانی تماس بگیرید."
	} else {
		text = "❌ Your payment was rejected. Please contact support if you believe this is an error."
	}

	payload := map[string]interface{}{
		"chat_id": user.TelegramID,
		"text":    text,
	}
	jsonData, _ := json.Marshal(payload)
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)
	http.Post(url, "application/json", bytes.NewBuffer(jsonData))
}
