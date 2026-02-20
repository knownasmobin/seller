package controllers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetOrCreateUserRequest represents the body of the GetOrCreateUser API
type GetOrCreateUserRequest struct {
	TelegramID int64  `json:"telegram_id"`
	Language   string `json:"language"`
}

// GetOrCreateUser handles fetching a user or creating one if they don't exist
// @Summary Fetch or create a user
// @Description Fetches a user by telegram_id, creates one if it doesn't exist
// @Tags Users
// @Accept json
// @Produce json
// @Param request body GetOrCreateUserRequest true "User Details"
// @Success 200 {object} models.User
// @Router /users [post]
func GetOrCreateUser(c *fiber.Ctx) error {
	var req GetOrCreateUserRequest
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

// UpdateUserBalanceRequest represents the body of the UpdateUserBalance API
type UpdateUserBalanceRequest struct {
	Amount float64 `json:"amount"`
}

// UpdateUserBalance allows modifying user balance (add/subtract)
// @Summary Update user balance
// @Description Adds or subtracts balance from a user's account
// @Tags Users
// @Accept json
// @Produce json
// @Param telegram_id path int64 true "Telegram User ID"
// @Param request body UpdateUserBalanceRequest true "Amount to update"
// @Success 200 {object} models.User
// @Router /users/{telegram_id}/balance [patch]
func UpdateUserBalance(c *fiber.Ctx) error {
	telegramID := c.Params("telegram_id")

	var req UpdateUserBalanceRequest
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
