package controllers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetActivePlans returns all active plans, optionally filtered by server_type
// @Summary Get active plans
// @Description Returns all active plans, optionally filtered by server_type (v2ray or wireguard)
// @Tags Plans
// @Produce json
// @Param type query string false "Server type (v2ray or wireguard)"
// @Success 200 {array} models.Plan
// @Router /plans [get]
func GetActivePlans(c *fiber.Ctx) error {
	serverType := c.Query("type") // e.g., ?type=v2ray
	showAll := c.Query("all") == "true"

	var plans []models.Plan
	query := database.DB

	if !showAll {
		query = query.Where("is_active = ?", true)
	}

	if serverType != "" {
		query = query.Where("server_type = ?", serverType)
	}

	if err := query.Find(&plans).Error; err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to fetch plans"})
	}

	return c.JSON(plans)
}

// GetPlan returns a specific plan by ID
// @Summary Get plan by ID
// @Description Returns a plan by ID
// @Tags Plans
// @Produce json
// @Param id path int true "Plan ID"
// @Success 200 {object} models.Plan
// @Router /plans/{id} [get]
func GetPlan(c *fiber.Ctx) error {
	planID := c.Params("id")
	var plan models.Plan

	if err := database.DB.First(&plan, planID).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Plan not found"})
	}

	return c.JSON(plan)
}

// CreatePlan Admin endpoint to create new plans
// @Summary Create a new plan
// @Description Admin endpoint to create new plans
// @Tags Plans
// @Accept json
// @Produce json
// @Param request body models.Plan true "Plan Details"
// @Success 201 {object} models.Plan
// @Router /plans [post]
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

// UpdatePlanRequest represents fields that can be edited
type UpdatePlanRequest struct {
	DurationDays *int     `json:"duration_days"`
	DataLimitGB  *float64 `json:"data_limit_gb"`
	PriceIRR     *float64 `json:"price_irr"`
	PriceUSDT    *float64 `json:"price_usdt"`
	IsActive     *bool    `json:"is_active"`
}

// UpdatePlan modifies an existing plan
// @Summary Edit an existing plan
// @Description Admin endpoint to edit an existing plan
// @Tags Plans
// @Accept json
// @Produce json
// @Param id path int true "Plan ID"
// @Param request body UpdatePlanRequest true "Plan Update Details"
// @Success 200 {object} models.Plan
// @Router /plans/{id} [patch]
func UpdatePlan(c *fiber.Ctx) error {
	planID := c.Params("id")

	var plan models.Plan
	if err := database.DB.First(&plan, planID).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "Plan not found"})
	}

	var req UpdatePlanRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	if req.DurationDays != nil {
		plan.DurationDays = *req.DurationDays
	}
	if req.DataLimitGB != nil {
		plan.DataLimitGB = *req.DataLimitGB
	}
	if req.PriceIRR != nil {
		plan.PriceIRR = *req.PriceIRR
	}
	if req.PriceUSDT != nil {
		plan.PriceUSDT = *req.PriceUSDT
	}
	if req.IsActive != nil {
		plan.IsActive = *req.IsActive
	}

	database.DB.Save(&plan)
	return c.JSON(plan)
}
