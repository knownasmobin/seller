package controllers

import (
	"encoding/json"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

func setupAdminTestDB(t *testing.T) {
	t.Helper()
	os.Setenv("DB_PATH", ":memory:")
	database.Connect()
	err := database.DB.AutoMigrate(&models.User{})
	if err != nil {
		t.Fatalf("failed to migrate test db: %v", err)
	}
	database.DB.Unscoped().Where("1 = 1").Delete(&models.User{})
}

func setupAdminApp() *fiber.App {
	app := fiber.New()
	app.Post("/admin/users/:telegram_id/message", SendMessageToUser)
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

