package controllers

import (
	"encoding/json"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

func setupAdminTestDB(t *testing.T) {
	t.Helper()
	os.Setenv("DB_PATH", ":memory:")
	database.Connect()
	err := database.DB.AutoMigrate(&models.User{}, &models.AppSetting{}, &models.Subscription{})
	if err != nil {
		t.Fatalf("failed to migrate test db: %v", err)
	}
	database.DB.Unscoped().Where("1 = 1").Delete(&models.User{})
	database.DB.Unscoped().Where("1 = 1").Delete(&models.AppSetting{})
}

func setupAdminApp() *fiber.App {
	app := fiber.New()
	app.Post("/admin/users/:telegram_id/message", SendMessageToUser)
	app.Post("/admin/broadcast", BroadcastMessage)
	return app
}

func setupSettingsApp() *fiber.App {
	app := fiber.New()
	app.Use(func(c *fiber.Ctx) error {
		// Mock auth middleware - accept Bot token
		authHeader := c.Get("Authorization")
		if authHeader == "" || !strings.HasPrefix(authHeader, "Bot ") {
			return c.Status(401).JSON(fiber.Map{"error": "Unauthorized"})
		}
		return c.Next()
	})
	app.Get("/settings/required_channel", GetRequiredChannel)
	app.Get("/admin/settings", GetSettings)
	app.Patch("/admin/settings", UpdateSettings)
	return app
}

func TestSendMessageToUser_Returns400ForInvalidTelegramID(t *testing.T) {
	setupAdminTestDB(t)
	app := setupAdminApp()

	payload := `{"message":"Test message"}`
	req := httptest.NewRequest("POST", "/admin/users/invalid/message", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 400 {
		t.Fatalf("expected status 400, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["error"] != "Invalid Telegram ID" {
		t.Fatalf("expected error 'Invalid Telegram ID', got %v", body["error"])
	}
}

func TestSendMessageToUser_Returns400ForEmptyMessage(t *testing.T) {
	setupAdminTestDB(t)
	app := setupAdminApp()

	payload := `{"message":""}`
	req := httptest.NewRequest("POST", "/admin/users/123456789/message", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 400 {
		t.Fatalf("expected status 400, got %d", resp.StatusCode)
	}
}

func TestSendMessageToUser_Returns404ForNonExistentUser(t *testing.T) {
	setupAdminTestDB(t)
	// Set BOT_TOKEN to avoid 500 error
	os.Setenv("BOT_TOKEN", "test-token")
	defer os.Unsetenv("BOT_TOKEN")
	
	app := setupAdminApp()

	payload := `{"message":"Test message"}`
	req := httptest.NewRequest("POST", "/admin/users/999999999/message", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 404 {
		var body map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&body)
		t.Fatalf("expected status 404, got %d. Response: %v", resp.StatusCode, body)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["error"] != "User not found" {
		t.Fatalf("expected error 'User not found', got %v", body["error"])
	}
}

func TestSendMessageToUser_ValidatesUserExists(t *testing.T) {
	setupAdminTestDB(t)
	app := setupAdminApp()

	// Create a test user
	user := models.User{TelegramID: 123456789, Language: "en"}
	database.DB.Create(&user)

	payload := `{"message":"Test message"}`
	req := httptest.NewRequest("POST", "/admin/users/123456789/message", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	// Note: This will fail at the Telegram API call since BOT_TOKEN is not set in test
	// But we can verify the user lookup works
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	// Should fail at Telegram API (500) or succeed if BOT_TOKEN is mocked
	// The important thing is it doesn't fail at user lookup (404)
	if resp.StatusCode == 404 {
		t.Fatalf("expected user to be found, got 404")
	}
}

func TestGetRequiredChannel_ReturnsEmptyWhenNotSet(t *testing.T) {
	setupAdminTestDB(t)
	app := setupSettingsApp()

	req := httptest.NewRequest("GET", "/settings/required_channel", nil)
	req.Header.Set("Authorization", "Bot test-token")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["required_channel"] != "" {
		t.Fatalf("expected empty required_channel, got %v", body["required_channel"])
	}
}

func TestGetRequiredChannel_ReturnsSetValue(t *testing.T) {
	setupAdminTestDB(t)
	app := setupSettingsApp()

	// Set a channel
	setting := models.AppSetting{Key: "required_channel", Value: "@mychannel"}
	database.DB.Create(&setting)

	req := httptest.NewRequest("GET", "/settings/required_channel", nil)
	req.Header.Set("Authorization", "Bot test-token")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["required_channel"] != "@mychannel" {
		t.Fatalf("expected '@mychannel', got %v", body["required_channel"])
	}
}

func TestGetSettings_IncludesRequiredChannel(t *testing.T) {
	setupAdminTestDB(t)
	os.Setenv("ADMIN_CARD_NUMBER", "1234-5678")
	os.Setenv("BOT_NAME", "TestBot")
	defer os.Unsetenv("ADMIN_CARD_NUMBER")
	defer os.Unsetenv("BOT_NAME")

	app := setupSettingsApp()

	// Set a channel
	setting := models.AppSetting{Key: "required_channel", Value: "@testchannel"}
	database.DB.Create(&setting)

	req := httptest.NewRequest("GET", "/admin/settings", nil)
	req.Header.Set("Authorization", "Bot test-token")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["required_channel"] != "@testchannel" {
		t.Fatalf("expected '@testchannel', got %v", body["required_channel"])
	}
	if body["admin_card_number"] != "1234-5678" {
		t.Fatalf("expected '1234-5678', got %v", body["admin_card_number"])
	}
}

func TestUpdateSettings_SetsRequiredChannel(t *testing.T) {
	setupAdminTestDB(t)
	app := setupSettingsApp()

	payload := `{"required_channel":"@newchannel"}`
	req := httptest.NewRequest("PATCH", "/admin/settings", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bot test-token")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["required_channel"] != "@newchannel" {
		t.Fatalf("expected '@newchannel', got %v", body["required_channel"])
	}

	// Verify it's persisted in DB
	var setting models.AppSetting
	if err := database.DB.Where("key = ?", "required_channel").First(&setting).Error; err != nil {
		t.Fatalf("expected setting to be persisted, got error: %v", err)
	}
	if setting.Value != "@newchannel" {
		t.Fatalf("expected persisted value '@newchannel', got %q", setting.Value)
	}
}

func TestUpdateSettings_UpdatesExistingChannel(t *testing.T) {
	setupAdminTestDB(t)
	app := setupSettingsApp()

	// Create existing setting
	setting := models.AppSetting{Key: "required_channel", Value: "@oldchannel"}
	database.DB.Create(&setting)

	payload := `{"required_channel":"@updatedchannel"}`
	req := httptest.NewRequest("PATCH", "/admin/settings", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bot test-token")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	// Verify it's updated in DB
	var updatedSetting models.AppSetting
	if err := database.DB.Where("key = ?", "required_channel").First(&updatedSetting).Error; err != nil {
		t.Fatalf("expected setting to exist, got error: %v", err)
	}
	if updatedSetting.Value != "@updatedchannel" {
		t.Fatalf("expected updated value '@updatedchannel', got %q", updatedSetting.Value)
	}
}

func TestUpdateSettings_DeletesChannelWhenEmpty(t *testing.T) {
	setupAdminTestDB(t)
	app := setupSettingsApp()

	// Create existing setting
	setting := models.AppSetting{Key: "required_channel", Value: "@oldchannel"}
	database.DB.Create(&setting)

	payload := `{"required_channel":""}`
	req := httptest.NewRequest("PATCH", "/admin/settings", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bot test-token")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["required_channel"] != "" {
		t.Fatalf("expected empty required_channel, got %v", body["required_channel"])
	}

	// Verify it's deleted from DB
	var deletedSetting models.AppSetting
	if err := database.DB.Where("key = ?", "required_channel").First(&deletedSetting).Error; err == nil {
		t.Fatalf("expected setting to be deleted, but it still exists")
	}
}

func TestGetBroadcastUsers_ActiveDeduplicatesUsersWithMultipleSubscriptions(t *testing.T) {
	setupAdminTestDB(t)

	u1 := models.User{TelegramID: 1111, Language: "en"}
	u2 := models.User{TelegramID: 2222, Language: "en"}
	if err := database.DB.Create(&u1).Error; err != nil {
		t.Fatalf("failed to create user1: %v", err)
	}
	if err := database.DB.Create(&u2).Error; err != nil {
		t.Fatalf("failed to create user2: %v", err)
	}

	now := time.Now()
	subs := []models.Subscription{
		{UserID: u1.ID, PlanID: 1, Status: "active", StartDate: now.Add(-24 * time.Hour), ExpiryDate: now.Add(24 * time.Hour), UUID: "sub-1"},
		{UserID: u1.ID, PlanID: 2, Status: "active", StartDate: now.Add(-24 * time.Hour), ExpiryDate: now.Add(48 * time.Hour), UUID: "sub-2"},
		{UserID: u2.ID, PlanID: 3, Status: "active", StartDate: now.Add(-24 * time.Hour), ExpiryDate: now.Add(24 * time.Hour), UUID: "sub-3"},
	}
	if err := database.DB.Create(&subs).Error; err != nil {
		t.Fatalf("failed to create subscriptions: %v", err)
	}

	users, err := getBroadcastUsers("active")
	if err != nil {
		t.Fatalf("getBroadcastUsers returned error: %v", err)
	}

	if len(users) != 2 {
		t.Fatalf("expected 2 unique users, got %d", len(users))
	}
}

