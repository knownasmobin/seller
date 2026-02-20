package database

import (
	"encoding/json"
	"log"
	"os"

	"github.com/username/sell-bot-backend/models"
)

// SeedServers checks if the servers table is empty and populates it with .env variables if present
func SeedServers() {
	var count int64
	DB.Model(&models.Server{}).Count(&count)

	if count > 0 {
		return // Servers already exist, skip seeding
	}

	log.Println("No servers found. Attempting to seed from environment variables...")

	marzbanURL := os.Getenv("MARZBAN_URL")
	marzbanUser := os.Getenv("MARZBAN_USERNAME")
	marzbanPass := os.Getenv("MARZBAN_PASSWORD")

	if marzbanURL != "" && marzbanUser != "" && marzbanPass != "" {
		creds, _ := json.Marshal(map[string]string{
			"username": marzbanUser,
			"password": marzbanPass,
		})

		marzbanServer := models.Server{
			Name:        "Default Marzban",
			ServerType:  "v2ray",
			APIUrl:      marzbanURL,
			Credentials: string(creds),
			IsActive:    true,
		}
		DB.Create(&marzbanServer)
		log.Println("Seeded default Marzban server.")
	}

	wgURL := os.Getenv("WGPORTAL_URL")
	wgUser := os.Getenv("WGPORTAL_USERNAME")
	wgPass := os.Getenv("WGPORTAL_PASSWORD")

	if wgURL != "" && wgUser != "" && wgPass != "" {
		creds, _ := json.Marshal(map[string]string{
			"username": wgUser,
			"password": wgPass,
		})

		wgServer := models.Server{
			Name:        "Default WireGuard",
			ServerType:  "wireguard",
			APIUrl:      wgURL,
			Credentials: string(creds),
			IsActive:    true,
		}
		DB.Create(&wgServer)
		log.Println("Seeded default WireGuard server.")
	}
}
