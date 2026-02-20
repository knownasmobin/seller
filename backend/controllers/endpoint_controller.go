package controllers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetEndpoints returns all active endpoints
func GetEndpoints(c *fiber.Ctx) error {
	showAll := c.Query("all") == "true"

	var endpoints []models.Endpoint
	query := database.DB

	if !showAll {
		query = query.Where("is_active = ?", true)
	}

	query.Find(&endpoints)
	return c.JSON(endpoints)
}

// GetEndpoint returns a specific endpoint by ID
func GetEndpoint(c *fiber.Ctx) error {
	id := c.Params("id")
	var endpoint models.Endpoint
	if err := database.DB.First(&endpoint, id).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Endpoint not found"})
	}
	return c.JSON(endpoint)
}

// CreateEndpoint creates a new WireGuard endpoint
func CreateEndpoint(c *fiber.Ctx) error {
	endpoint := new(models.Endpoint)
	if err := c.BodyParser(endpoint); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if err := database.DB.Create(&endpoint).Error; err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to create endpoint"})
	}

	return c.Status(201).JSON(endpoint)
}

// UpdateEndpoint modifies an existing endpoint
func UpdateEndpoint(c *fiber.Ctx) error {
	id := c.Params("id")

	var endpoint models.Endpoint
	if err := database.DB.First(&endpoint, id).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Endpoint not found"})
	}

	type UpdateReq struct {
		Name     *string `json:"name"`
		Address  *string `json:"address"`
		IsActive *bool   `json:"is_active"`
	}

	var req UpdateReq
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if req.Name != nil {
		endpoint.Name = *req.Name
	}
	if req.Address != nil {
		endpoint.Address = *req.Address
	}
	if req.IsActive != nil {
		endpoint.IsActive = *req.IsActive
	}

	database.DB.Save(&endpoint)
	return c.JSON(endpoint)
}

// DeleteEndpoint soft-deletes an endpoint
func DeleteEndpoint(c *fiber.Ctx) error {
	id := c.Params("id")

	var endpoint models.Endpoint
	if err := database.DB.First(&endpoint, id).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Endpoint not found"})
	}

	database.DB.Delete(&endpoint)
	return c.JSON(fiber.Map{"message": "Endpoint deleted"})
}
