package controllers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetActivePlans returns all active plans, optionally filtered by server_type
func GetActivePlans(c *fiber.Ctx) error {
	serverType := c.Query("type") // e.g., ?type=v2ray

	var plans []models.Plan
	query := database.DB.Where("is_active = ?", true)

	if serverType != "" {
		query = query.Where("server_type = ?", serverType)
	}

	if err := query.Find(&plans).Error; err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to fetch plans"})
	}

	return c.JSON(plans)
}

// CreatePlan Admin endpoint to create new plans
func CreatePlan(c *fiber.Ctx) error {
	plan := new(models.Plan)
	if err := c.BodyParser(plan); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if err := database.DB.Create(&plan).Error; err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to create plan"})
	}

	return c.Status(201).JSON(plan)
}
