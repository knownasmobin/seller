package controllers

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// Simple in-memory token store
var (
	validTokens = make(map[string]time.Time)
	tokenMu     sync.RWMutex
)

func generateToken() string {
	b := make([]byte, 32)
	rand.Read(b)
	return hex.EncodeToString(b)
}

// AdminLogin validates the dashboard password and returns a session token
func AdminLogin(c *fiber.Ctx) error {
	type LoginReq struct {
		Password string `json:"password"`
	}

	var req LoginReq
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request"})
	}

	adminPass := os.Getenv("ADMIN_DASHBOARD_PASSWORD")
	if adminPass == "" {
		adminPass = "admin123" // fallback default
	}

	if req.Password != adminPass {
		return c.Status(401).JSON(fiber.Map{"error": "Invalid password"})
	}

	token := generateToken()
	tokenMu.Lock()
	validTokens[token] = time.Now().Add(24 * time.Hour)
	tokenMu.Unlock()

	return c.JSON(fiber.Map{
		"token":   token,
		"message": "Login successful",
	})
}

// AdminAuthMiddleware checks for a valid Bearer token on admin routes
func AdminAuthMiddleware(c *fiber.Ctx) error {
	authHeader := c.Get("Authorization")
	if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
		return c.Status(401).JSON(fiber.Map{"error": "Unauthorized"})
	}

	token := strings.TrimPrefix(authHeader, "Bearer ")

	tokenMu.RLock()
	expiry, exists := validTokens[token]
	tokenMu.RUnlock()

	if !exists || time.Now().After(expiry) {
		return c.Status(401).JSON(fiber.Map{"error": "Session expired"})
	}

	return c.Next()
}

// GetAdminStats returns aggregate statistics for the admin dashboard
// @Summary Get admin dashboard statistics
// @Description Returns user, order, plan, subscription counts and revenue
// @Tags Admin
// @Produce json
// @Success 200 {object} map[string]interface{}
// @Router /admin/stats [get]
func GetAdminStats(c *fiber.Ctx) error {
	var totalUsers int64
	database.DB.Model(&models.User{}).Count(&totalUsers)

	var totalOrders int64
	database.DB.Model(&models.Order{}).Count(&totalOrders)

	var paidOrders int64
	database.DB.Model(&models.Order{}).Where("payment_status IN (?)", []string{"paid", "approved"}).Count(&paidOrders)

	var pendingOrders int64
	database.DB.Model(&models.Order{}).Where("payment_status = ?", "pending").Count(&pendingOrders)

	var activePlans int64
	database.DB.Model(&models.Plan{}).Where("is_active = ?", true).Count(&activePlans)

	var activeSubscriptions int64
	database.DB.Model(&models.Subscription{}).Where("status = ? AND expiry_date > ?", "active", time.Now()).Count(&activeSubscriptions)

	// Revenue — orders can be status "paid" (crypto auto) or "approved" (card manual)
	var totalRevenueIRR float64
	database.DB.Model(&models.Order{}).Where("payment_status IN (?) AND payment_method = ?", []string{"paid", "approved"}, "card").Select("COALESCE(SUM(amount), 0)").Scan(&totalRevenueIRR)

	var totalRevenueUSDT float64
	database.DB.Model(&models.Order{}).Where("payment_status IN (?) AND payment_method = ?", []string{"paid", "approved"}, "crypto").Select("COALESCE(SUM(amount), 0)").Scan(&totalRevenueUSDT)

	// Recent orders (last 10)
	type RecentOrder struct {
		ID            uint      `json:"id"`
		UserID        uint      `json:"user_id"`
		TelegramID    int64     `json:"telegram_id"`
		PlanID        uint      `json:"plan_id"`
		Amount        float64   `json:"amount"`
		PaymentMethod string    `json:"payment_method"`
		PaymentStatus string    `json:"payment_status"`
		CreatedAt     time.Time `json:"created_at"`
	}

	var recentOrders []RecentOrder
	database.DB.Table("orders").
		Select("orders.id, orders.user_id, users.telegram_id, orders.plan_id, orders.amount, orders.payment_method, orders.payment_status, orders.created_at").
		Joins("LEFT JOIN users ON users.id = orders.user_id").
		Where("orders.deleted_at IS NULL").
		Order("orders.created_at DESC").
		Limit(10).
		Scan(&recentOrders)

	return c.JSON(fiber.Map{
		"total_users":          totalUsers,
		"total_orders":         totalOrders,
		"paid_orders":          paidOrders,
		"pending_orders":       pendingOrders,
		"active_plans":         activePlans,
		"active_subscriptions": activeSubscriptions,
		"total_revenue_irr":    totalRevenueIRR,
		"total_revenue_usdt":   totalRevenueUSDT,
		"recent_orders":        recentOrders,
	})
}

// BroadcastMessage sends a Telegram message to users
// @Summary Broadcast a message to users
// @Description Sends a message to all users or active subscribers via Telegram Bot API
// @Tags Admin
// @Accept json
// @Produce json
// @Param body body object true "Broadcast request" SchemaExample({"message": "Hello!", "target": "all"})
// @Success 200 {object} map[string]interface{}
// @Router /admin/broadcast [post]
func BroadcastMessage(c *fiber.Ctx) error {
	type BroadcastRequest struct {
		Message string `json:"message"`
		Target  string `json:"target"` // "all" or "active"
	}

	var req BroadcastRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if strings.TrimSpace(req.Message) == "" {
		return c.Status(400).JSON(fiber.Map{"error": "Message cannot be empty"})
	}

	botToken := os.Getenv("BOT_TOKEN")
	if botToken == "" {
		return c.Status(500).JSON(fiber.Map{"error": "BOT_TOKEN not configured"})
	}

	// Get target users
	var users []models.User
	if req.Target == "active" {
		// Users with at least one active, non-expired subscription
		database.DB.Where("id IN (?)",
			database.DB.Table("subscriptions").
				Select("user_id").
				Where("status = ? AND expiry_date > ?", "active", time.Now()),
		).Find(&users)
	} else {
		database.DB.Find(&users)
	}

	sent := 0
	failed := 0

	for _, user := range users {
		err := sendTelegramMessage(botToken, user.TelegramID, req.Message)
		if err != nil {
			log.Printf("[Broadcast] Failed to send to %d: %v", user.TelegramID, err)
			failed++
		} else {
			sent++
		}
	}

	return c.JSON(fiber.Map{
		"sent":   sent,
		"failed": failed,
		"total":  len(users),
	})
}

func sendTelegramMessage(botToken string, chatID int64, message string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)

	payload := fmt.Sprintf(`{"chat_id":%d,"text":%q,"parse_mode":"Markdown"}`, chatID, message)
	resp, err := http.Post(url, "application/json", strings.NewReader(payload))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := ioutil.ReadAll(resp.Body)
		return fmt.Errorf("telegram API error: %s", string(body))
	}

	return nil
}

// GetServers returns all server configurations
func GetServers(c *fiber.Ctx) error {
	var servers []models.Server
	database.DB.Find(&servers)
	return c.JSON(servers)
}

// UpdateServer updates a server's connection details
func UpdateServer(c *fiber.Ctx) error {
	id := c.Params("id")

	var server models.Server
	if err := database.DB.First(&server, id).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Server not found"})
	}

	type UpdateReq struct {
		Name        *string `json:"name"`
		APIUrl      *string `json:"api_url"`
		Credentials *string `json:"credentials"` // JSON string: {"username":"..","password":".."}
		IsActive    *bool   `json:"is_active"`
	}

	var req UpdateReq
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if req.Name != nil {
		server.Name = *req.Name
	}
	if req.APIUrl != nil {
		server.APIUrl = *req.APIUrl
	}
	if req.Credentials != nil {
		server.Credentials = *req.Credentials
	}
	if req.IsActive != nil {
		server.IsActive = *req.IsActive
	}

	database.DB.Save(&server)
	return c.JSON(server)
}

// GetSettings returns current bot settings (card number, etc.)
func GetSettings(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"admin_card_number": os.Getenv("ADMIN_CARD_NUMBER"),
		"bot_name":          os.Getenv("BOT_NAME"),
	})
}

// UpdateSettings updates bot settings by writing to a settings file
// Note: env vars can't be changed at runtime in production.
// For a real solution, store settings in DB. For now, return guidance.
func UpdateSettings(c *fiber.Ctx) error {
	type SettingsReq struct {
		AdminCardNumber string `json:"admin_card_number"`
	}

	var req SettingsReq
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if req.AdminCardNumber != "" {
		os.Setenv("ADMIN_CARD_NUMBER", req.AdminCardNumber)
	}

	return c.JSON(fiber.Map{
		"message":           "Settings updated for this session",
		"admin_card_number": os.Getenv("ADMIN_CARD_NUMBER"),
	})
}
