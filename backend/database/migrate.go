package database

import (
	"log"

	"github.com/username/sell-bot-backend/models"
)

func Migrate() {
	err := DB.AutoMigrate(
		&models.User{},
		&models.Server{},
		&models.Plan{},
		&models.Order{},
		&models.Subscription{},
		&models.Endpoint{},
	)
	if err != nil {
		log.Fatal("Failed to migrate database: \n", err)
	}
	log.Println("Database migration completed")
}
