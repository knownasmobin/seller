package routes

import (
	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/controllers"

	"github.com/gofiber/swagger"
	_ "github.com/username/sell-bot-backend/docs"
)

func SetupRoutes(router fiber.Router) {
	router.Get("/", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"status":  "success",
			"message": "Welcome to the VPN Sell Bot API",
		})
	})

	// Swagger Documentation
	router.Get("/swagger/*", swagger.HandlerDefault)

	// User Routes
	users := router.Group("/users")
	users.Post("/", controllers.GetOrCreateUser)
	users.Patch("/:telegram_id/balance", controllers.UpdateUserBalance)
	users.Patch("/:telegram_id/language", controllers.UpdateUserLanguage)

	// Plan Routes
	plans := router.Group("/plans")
	plans.Get("/", controllers.GetActivePlans)
	plans.Get("/:id", controllers.GetPlan)
	plans.Post("/", controllers.CreatePlan)
	plans.Patch("/:id", controllers.UpdatePlan)

	// Order Routes
	orders := router.Group("/orders")
	orders.Post("/", controllers.CreateOrder)
	orders.Post("/:id/approve", controllers.ApproveOrder)
	orders.Post("/:id/reject", controllers.RejectOrder)
	users.Get("/:telegram_id/orders", controllers.GetUserOrders) // Note attached to users group
	users.Get("/:telegram_id/subscriptions", controllers.GetUserSubscriptions)

	// Webhook Routes
	webhooks := router.Group("/webhooks")
	webhooks.Post("/oxapay", controllers.OxapayCallback)
}
