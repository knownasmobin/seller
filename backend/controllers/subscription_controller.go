package controllers

import (
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
	"github.com/username/sell-bot-backend/vpn"
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

	// ...

	return c.JSON(subscriptions)
}

// GetWGConfig returns the transformed wireguard config for a specific subscription and endpoint
// @Summary Get transformed WG config
// @Description Returns the transformed wireguard config
// @Tags Subscriptions
// @Produce json
// @Param telegram_id path int64 true "Telegram User ID"
// @Param sub_id path int true "Subscription ID"
// @Param endpoint_id query int false "Endpoint ID"
// @Success 200 {object} map[string]interface{}
// @Router /users/{telegram_id}/subscriptions/{sub_id}/wg_config [get]
func GetWGConfig(c *fiber.Ctx) error {
	telegramID := c.Params("telegram_id")
	subID := c.Params("sub_id")
	endpointID := c.Query("endpoint_id")

	var user models.User
	if err := database.DB.Where("telegram_id = ?", telegramID).First(&user).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "User not found"})
	}

	var sub models.Subscription
	if err := database.DB.Where("id = ? AND user_id = ?", subID, user.ID).First(&sub).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Subscription not found"})
	}

	endpointAddr := ""
	if endpointID != "" {
		var ep models.Endpoint
		if err := database.DB.Where("id = ?", endpointID).First(&ep).Error; err == nil {
			endpointAddr = ep.Address
		}
	}

	botName := os.Getenv("BOT_NAME")
	if botName == "" {
		botName = "ghostwire t.me/theghostwirebot"
	}
	wireSockApps := os.Getenv("WIRESOCK_ALLOWED_APPS")

	// sub.ConfigLink holds the raw wgportal config
	transformed := vpn.TransformWGConfig(sub.ConfigLink, botName, endpointAddr, wireSockApps)

	return c.JSON(fiber.Map{
		"uuid":   sub.UUID,
		"config": transformed,
	})
}
