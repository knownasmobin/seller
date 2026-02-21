package controllers

import (
	"encoding/json"
	"io/ioutil"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

func setupTestDB() {
	os.Setenv("DB_PATH", "file::memory:?cache=shared")
	database.Connect()
	database.DB.AutoMigrate(&models.Order{}, &models.User{}, &models.Plan{}, &models.Subscription{}, &models.Server{})
}

func setupFiberApp() *fiber.App {
	app := fiber.New()
	app.Post("/orders/:id/reject", RejectOrder)
	return app
}

func TestRejectOrder(t *testing.T) {
	setupTestDB()
	app := setupFiberApp()

	// Seed data
	user := models.User{TelegramID: 123456789, Language: "en"}
	database.DB.Create(&user)

	order := models.Order{
		UserID:        user.ID,
		Amount:        10.5,
		PaymentStatus: "pending",
		CreatedAt:     time.Now(),
	}
	database.DB.Create(&order)

	// Build request
	req := httptest.NewRequest("POST", "/orders/1/reject", nil)
	resp, err := app.Test(req, -1)

	if err != nil {
		t.Fatalf("Failed to execute request: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("Expected status code 200, got %d", resp.StatusCode)
	}

	// Verify Database Update
	var updatedOrder models.Order
	database.DB.First(&updatedOrder, order.ID)

	if updatedOrder.PaymentStatus != "rejected" {
		t.Errorf("Expected order status to be 'rejected', got '%s'", updatedOrder.PaymentStatus)
	}

	// Check Response Body
	bodyBytes, _ := ioutil.ReadAll(resp.Body)
	var responseBody map[string]interface{}
	json.Unmarshal(bodyBytes, &responseBody)

	if responseBody["message"] != "Order rejected" {
		t.Errorf("Expected message 'Order rejected', got %v", responseBody["message"])
	}
}
