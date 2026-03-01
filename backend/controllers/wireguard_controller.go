package controllers

import (
	"os"
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

const wireSockAllowedAppsKey = "wiresock_allowed_apps"

func getSettingValue(key string) (string, bool) {
	var setting models.AppSetting
	if err := database.DB.Where("key = ?", key).First(&setting).Error; err != nil {
		return "", false
	}
	return setting.Value, true
}

func setSettingValue(key, value string) error {
	var setting models.AppSetting
	err := database.DB.Where("key = ?", key).First(&setting).Error
	if err != nil {
		setting = models.AppSetting{Key: key, Value: value}
		return database.DB.Create(&setting).Error
	}

	setting.Value = value
	return database.DB.Save(&setting).Error
}

func getWireSockAllowedApps() string {
	if value, ok := getSettingValue(wireSockAllowedAppsKey); ok && strings.TrimSpace(value) != "" {
		return value
	}
	return os.Getenv("WIRESOCK_ALLOWED_APPS")
}

// GetWireGuardDashboard returns runtime WireGuard dashboard settings and endpoint list.
func GetWireGuardDashboard(c *fiber.Ctx) error {
	var endpoints []models.Endpoint
	database.DB.Find(&endpoints)

	return c.JSON(fiber.Map{
		"wiresock_allowed_apps": getWireSockAllowedApps(),
		"endpoints":            endpoints,
	})
}

// UpdateWireGuardSettings updates runtime WireGuard settings (currently wiresock_allowed_apps).
func UpdateWireGuardSettings(c *fiber.Ctx) error {
	type UpdateReq struct {
		WireSockAllowedApps *string `json:"wiresock_allowed_apps"`
	}

	var req UpdateReq
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if req.WireSockAllowedApps != nil {
		if err := setSettingValue(wireSockAllowedAppsKey, *req.WireSockAllowedApps); err != nil {
			return c.Status(500).JSON(fiber.Map{"error": "Failed to update WireGuard settings"})
		}
	}

	return c.JSON(fiber.Map{
		"message":               "WireGuard settings updated",
		"wiresock_allowed_apps": getWireSockAllowedApps(),
	})
}
