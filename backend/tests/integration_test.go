package tests

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/controllers"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

func setupTestDB() {
	os.Setenv("DB_PATH", "file::memory:?cache=shared")
	database.Connect()
	database.DB.AutoMigrate(&models.Order{}, &models.User{}, &models.Plan{}, &models.Subscription{}, &models.Server{})
}

func TestApproveOrderIntegration(t *testing.T) {
	setupTestDB()

	// 1. Create a mock Marzban server
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/admin/token" {
			// Mock Login
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(200)
			json.NewEncoder(w).Encode(map[string]interface{}{"access_token": "mock-token-123"})
			return
		}
		if r.URL.Path == "/api/user" {
			// Mock User Creation
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(200)
			json.NewEncoder(w).Encode(map[string]interface{}{
				"username":         "test-user",
				"subscription_url": "http://mock-marzban.local/sub/test-user/",
			})
			return
		}

		// If it's for Telegram bot mock
		if r.URL.Path == "/botMOCK_TOKEN/sendMessage" {
			w.WriteHeader(200)
			return
		}

		w.WriteHeader(404)
	}))
	defer mockServer.Close()

	os.Setenv("BOT_TOKEN", "MOCK_TOKEN")
	// If the backend has hardcoded telegram URL we can't intercept it unless we use httpmock,
	// but currently it just fails gracefully or prints. Let's ignore it.

	// 2. Seed database
	user := models.User{TelegramID: 11111, Language: "fa"}
	database.DB.Create(&user)

	plan := models.Plan{
		ServerType:   "v2ray",
		DurationDays: 30,
		DataLimitGB:  50,
		IsActive:     true,
	}
	database.DB.Create(&plan)

	credsJSON, _ := json.Marshal(map[string]string{"username": "admin", "password": "password"})
	server := models.Server{
		Name:        "DE-1",
		APIUrl:      mockServer.URL, // Inject the mock server here!
		ServerType:  "v2ray",
		Credentials: string(credsJSON),
		IsActive:    true,
	}
	database.DB.Create(&server)

	order := models.Order{
		UserID:        user.ID,
		PlanID:        plan.ID,
		Amount:        15.0,
		PaymentStatus: "pending",
		CreatedAt:     time.Now(),
	}
	database.DB.Create(&order)

	// 3. Setup Fiber
	app := fiber.New()
	app.Post("/orders/:id/approve", controllers.ApproveOrder)

	// 4. Send Request
	req := httptest.NewRequest("POST", fmt.Sprintf("/orders/%d/approve", order.ID), nil)
	resp, err := app.Test(req, -1)

	if err != nil {
		t.Fatalf("Failed to execute request: %v", err)
	}

	if resp.StatusCode != 200 {
		body, _ := ioutil.ReadAll(resp.Body)
		t.Fatalf("Expected status code 200, got %d. Body: %s", resp.StatusCode, string(body))
	}

	// 5. Verify Database updates
	var updatedOrder models.Order
	database.DB.First(&updatedOrder, order.ID)
	if updatedOrder.PaymentStatus != "approved" {
		t.Errorf("Expected order status 'approved', got '%s'", updatedOrder.PaymentStatus)
	}

	var sub models.Subscription
	if err := database.DB.Where("user_id = ? AND plan_id = ?", user.ID, plan.ID).First(&sub).Error; err != nil {
		t.Fatalf("Expected subscription to be created, but got error: %v", err)
	}

	if sub.Status != "active" {
		t.Errorf("Expected subscription 'active', got '%s'", sub.Status)
	}

	expectedUrl := "http://mock-marzban.local/sub/test-user/"
	if sub.ConfigLink != expectedUrl {
		t.Errorf("Expected config link '%s', got '%s'", expectedUrl, sub.ConfigLink)
	}
}
