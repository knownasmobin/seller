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

	// Webhook Routes (Public)
	webhooks := router.Group("/webhooks")
	webhooks.Post("/oxapay", controllers.OxapayCallback)

	// Admin Auth & Public Settings (no middleware)
	router.Post("/admin/login", controllers.AdminLogin)
	router.Get("/admin/settings", controllers.GetSettings)

	// Protected Route Group
	protected := router.Group("/", controllers.AuthMiddleware)

	// User Routes
	users := protected.Group("/users")
	users.Post("/", controllers.GetOrCreateUser)
	users.Patch("/:telegram_id/balance", controllers.UpdateUserBalance)
	users.Patch("/:telegram_id/language", controllers.UpdateUserLanguage)
	users.Get("/:telegram_id/orders", controllers.GetUserOrders)
	users.Get("/:telegram_id/subscriptions", controllers.GetUserSubscriptions)
	users.Get("/:telegram_id/subscriptions/:sub_id/wg_config", controllers.GetWGConfig)

	// Plan Routes
	plans := protected.Group("/plans")
	plans.Get("/", controllers.GetActivePlans)
	plans.Get("/:id", controllers.GetPlan)
	plans.Post("/", controllers.CreatePlan)
	plans.Patch("/:id", controllers.UpdatePlan)

	// Order Routes
	orders := protected.Group("/orders")
	orders.Post("/", controllers.CreateOrder)
	orders.Post("/:id/approve", controllers.ApproveOrder)
	orders.Post("/:id/manual_provision", controllers.ManualProvisionOrder)
	orders.Post("/:id/reject", controllers.RejectOrder)

	// WireGuard Endpoint Routes
	endpoints := protected.Group("/endpoints")
	endpoints.Get("/", controllers.GetEndpoints)
	endpoints.Get("/:id", controllers.GetEndpoint)
	endpoints.Post("/", controllers.CreateEndpoint)
	endpoints.Patch("/:id", controllers.UpdateEndpoint)
	endpoints.Delete("/:id", controllers.DeleteEndpoint)

	// Admin Routes (using the same generic AuthMiddleware)
	admin := protected.Group("/admin")
	admin.Get("/stats", controllers.GetAdminStats)
	admin.Post("/broadcast", controllers.BroadcastMessage)
	admin.Get("/servers", controllers.GetServers)
	admin.Patch("/servers/:id", controllers.UpdateServer)
	admin.Patch("/settings", controllers.UpdateSettings)
}
