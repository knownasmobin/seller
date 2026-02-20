package controllers

import (
	"fmt"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
	"github.com/username/sell-bot-backend/payment"
)

// CreateOrderRequest represents the body for CreateOrder API
type CreateOrderRequest struct {
	TelegramID    int64   `json:"telegram_id"`
	PlanID        uint    `json:"plan_id"`
	EndpointID    uint    `json:"endpoint_id"` // WireGuard endpoint selection
	ConfigName    string  `json:"config_name"`
	PaymentMethod string  `json:"payment_method"`
	Amount        float64 `json:"amount"`
}

// CreateOrder handles generating a new order for a user buying a plan
// @Summary Create an order
// @Description Creates an order and returns payment link if method is crypto
// @Tags Orders
// @Accept json
// @Produce json
// @Param request body CreateOrderRequest true "Order Details"
// @Success 201 {object} map[string]interface{}
// @Router /orders [post]
func CreateOrder(c *fiber.Ctx) error {
	var req CreateOrderRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	// 1. Find User
	var user models.User
	if err := database.DB.Where("telegram_id = ?", req.TelegramID).First(&user).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "User not found"})
	}

	// 2. Find Plan
	var plan models.Plan
	if err := database.DB.First(&plan, req.PlanID).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Plan not found"})
	}

	// 3. Create Order
	order := models.Order{
		UserID:        user.ID,
		PlanID:        plan.ID,
		EndpointID:    req.EndpointID,
		ConfigName:    req.ConfigName,
		Amount:        req.Amount,
		PaymentMethod: req.PaymentMethod,
		PaymentStatus: "pending",
	}

	if err := database.DB.Create(&order).Error; err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to create order"})
	}

	payLink := ""
	if req.PaymentMethod == "crypto" {
		merchantKey := os.Getenv("OXAPAY_MERCHANT_KEY")
		if merchantKey != "" {
			pmt := payment.NewOxapayClient(merchantKey)
			link, err := pmt.CreateInvoice(req.Amount, fmt.Sprintf("%d", order.ID), "user@example.com")
			if err == nil {
				payLink = link
			}
		}
	}

	return c.Status(201).JSON(fiber.Map{
		"ID":      order.ID, // backward compatibility for python
		"order":   order,
		"payLink": payLink,
	})
}

// GetUserOrders returns all orders for a given telegram ID
// @Summary Get all user orders
// @Description Returns all orders for a given Telegram ID
// @Tags Orders
// @Produce json
// @Param telegram_id path int64 true "Telegram User ID"
// @Success 200 {array} models.Order
// @Router /users/{telegram_id}/orders [get]
func GetUserOrders(c *fiber.Ctx) error {
	telegramID := c.Params("telegram_id")

	var user models.User
	if err := database.DB.Where("telegram_id = ?", telegramID).First(&user).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "User not found"})
	}

	var orders []models.Order
	database.DB.Where("user_id = ?", user.ID).Order("created_at desc").Find(&orders)

	return c.JSON(orders)
}
