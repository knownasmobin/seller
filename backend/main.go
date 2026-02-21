package main

import (
	"log"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/joho/godotenv"

	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/routes"
	"github.com/username/sell-bot-backend/worker"
)

func init() {
	// Load environment variables
	if err := godotenv.Load("../.env"); err != nil {
		godotenv.Load(".env") // Fallback
	}

	database.Connect()
	database.Migrate()
	database.SeedServers()

	// Start background workers
	worker.StartUsageMonitor()
}

// @title VPN Sell Bot API
// @version 1.0
// @description REST API for VPN Sell Bot Backend
// @host localhost:3000
// @BasePath /api/v1
func main() {
	app := fiber.New(fiber.Config{
		AppName: "VPN Sell Bot API v1.0",
	})

	// Middleware
	app.Use(logger.New())
	app.Use(recover.New())

	// API Routes
	api := app.Group("/api/v1")
	routes.SetupRoutes(api)

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	log.Printf("Starting server on port %s", port)
	log.Fatal(app.Listen(":" + port))
}
