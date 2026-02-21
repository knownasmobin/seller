package controllers

import (
	"os"
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

// GetOrCreateUserRequest represents the body of the GetOrCreateUser API
type GetOrCreateUserRequest struct {
	TelegramID int64  `json:"telegram_id"`
	Language   string `json:"language"`
	InviteCode string `json:"invite_code"`
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
	result := database.DB.Where("telegram_id = ?", req.TelegramID).First(&user)

	if result.Error != nil {
		// User doesn't exist, create new if invite code is valid
		if req.InviteCode == "" {
			return c.Status(401).JSON(fiber.Map{"error": "invite_code_required", "message": "This bot is invite-only."})
		}

		var invitedBy int64 = 0
		validInvite := false

		// 1. Check if invite code matches any Admin ID
		adminIDs := strings.Split(os.Getenv("ADMIN_ID"), ",")
		for _, aid := range adminIDs {
			if strings.TrimSpace(aid) == req.InviteCode {
				validInvite = true
				if parsedAdminID, err := strconv.ParseInt(strings.TrimSpace(aid), 10, 64); err == nil {
					invitedBy = parsedAdminID
				}
				break
			}
		}

		// 2. If not admin, check if the invite code matches an existing user's Telegram ID
		if !validInvite {
			var inviter models.User
			if err := database.DB.Where("telegram_id = ?", req.InviteCode).First(&inviter).Error; err == nil {
				validInvite = true
				invitedBy = inviter.TelegramID
			}
		}

		if !validInvite {
			return c.Status(400).JSON(fiber.Map{"error": "invalid_invite_code", "message": "The provided invite code is not valid."})
		}

		user = models.User{
			TelegramID: req.TelegramID,
			Language:   req.Language,
			InvitedBy:  invitedBy,
		}
		if err := database.DB.Create(&user).Error; err != nil {
			return c.Status(500).JSON(fiber.Map{"error": "Failed to create user"})
		}
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

// UpdateUserLanguageRequest represents the body of the UpdateUserLanguage API
type UpdateUserLanguageRequest struct {
	Language string `json:"language"`
}

// UpdateUserLanguage updates the language preference for a user
// @Summary Update user language
// @Description Updates the language preference for a user
// @Tags Users
// @Accept json
// @Produce json
// @Param telegram_id path int64 true "Telegram User ID"
// @Param request body UpdateUserLanguageRequest true "Language"
// @Success 200 {object} models.User
// @Router /users/{telegram_id}/language [patch]
func UpdateUserLanguage(c *fiber.Ctx) error {
	telegramID := c.Params("telegram_id")

	var req UpdateUserLanguageRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	var user models.User
	if err := database.DB.Where("telegram_id = ?", telegramID).First(&user).Error; err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "User not found"})
	}

	user.Language = req.Language
	database.DB.Save(&user)

	return c.JSON(user)
}
