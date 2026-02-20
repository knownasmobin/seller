package controllers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetOrCreateUser handles fetching a user or creating one if they don't exist
func GetOrCreateUser(c *fiber.Ctx) error {
	type Request struct {
		TelegramID int64  `json:"telegram_id"`
		Language   string `json:"language"`
	}

	var req Request
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	var user models.User
	result := database.DB.Where(&models.User{TelegramID: req.TelegramID}).FirstOrCreate(&user, models.User{
		TelegramID: req.TelegramID,
		Language:   req.Language,
	})

	if result.Error != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Database error"})
	}

	return c.JSON(user)
}

// UpdateUserBalance allows modifying user balance (add/subtract)
func UpdateUserBalance(c *fiber.Ctx) error {
	telegramID := c.Params("telegram_id")

	type Request struct {
		Amount float64 `json:"amount"`
	}

	var req Request
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	var user models.User
	if err := database.DB.Where("telegram_id = ?", telegramID).First(&user).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "User not found"})
	}

	user.Balance += req.Amount
	database.DB.Save(&user)

	return c.JSON(user)
}
