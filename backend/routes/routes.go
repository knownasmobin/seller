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
	users.Get("/:telegram_id/subscriptions/:sub_id/wg_config", controllers.GetWGConfig)

	// Webhook Routes
	webhooks := router.Group("/webhooks")
	webhooks.Post("/oxapay", controllers.OxapayCallback)

	// WireGuard Endpoint Routes (Admin managed)
	endpoints := router.Group("/endpoints")
	endpoints.Get("/", controllers.GetEndpoints)
	endpoints.Get("/:id", controllers.GetEndpoint)
	endpoints.Post("/", controllers.CreateEndpoint)
	endpoints.Patch("/:id", controllers.UpdateEndpoint)
	endpoints.Delete("/:id", controllers.DeleteEndpoint)

	// Admin Auth (public - no middleware)
	router.Post("/admin/login", controllers.AdminLogin)

	// Admin Routes (protected by auth middleware)
	admin := router.Group("/admin", controllers.AdminAuthMiddleware)
	admin.Get("/stats", controllers.GetAdminStats)
	admin.Post("/broadcast", controllers.BroadcastMessage)
	admin.Get("/servers", controllers.GetServers)
	admin.Patch("/servers/:id", controllers.UpdateServer)
	admin.Get("/settings", controllers.GetSettings)
	admin.Patch("/settings", controllers.UpdateSettings)
}
