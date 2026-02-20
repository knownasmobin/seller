package controllers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetUserSubscriptions returns all subscriptions for a given telegram ID
// @Summary Get all user subscriptions
// @Description Returns all subscriptions for a given Telegram ID
// @Tags Subscriptions
// @Produce json
// @Param telegram_id path int64 true "Telegram User ID"
// @Success 200 {array} models.Subscription
// @Router /users/{telegram_id}/subscriptions [get]
func GetUserSubscriptions(c *fiber.Ctx) error {
	telegramID := c.Params("telegram_id")

	var user models.User
	if err := database.DB.Where("telegram_id = ?", telegramID).First(&user).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "User not found"})
	}

	var subscriptions []models.Subscription
	database.DB.Where("user_id = ?", user.ID).Order("start_date desc").Find(&subscriptions)

	return c.JSON(subscriptions)
}
