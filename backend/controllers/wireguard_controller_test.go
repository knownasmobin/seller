package controllers

import (
	"encoding/json"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

func setupWireGuardTestDB(t *testing.T) {
	t.Helper()
	os.Setenv("DB_PATH", "file::memory:?cache=shared")
	database.Connect()
	err := database.DB.AutoMigrate(&models.AppSetting{}, &models.Endpoint{})
	if err != nil {
		t.Fatalf("failed to migrate test db: %v", err)
	}
	database.DB.Exec("DELETE FROM app_settings")
	database.DB.Exec("DELETE FROM endpoints")
}

func setupWireGuardApp() *fiber.App {
	app := fiber.New()
	app.Get("/admin/wireguard", GetWireGuardDashboard)
	app.Patch("/admin/wireguard", UpdateWireGuardSettings)
	return app
}

func TestGetWireGuardDashboard_UsesEnvFallbackWhenNoDBSetting(t *testing.T) {
	setupWireGuardTestDB(t)
	app := setupWireGuardApp()

	expected := "chrome.exe,telegram.exe"
	os.Setenv("WIRESOCK_ALLOWED_APPS", expected)
	defer os.Unsetenv("WIRESOCK_ALLOWED_APPS")

	req := httptest.NewRequest("GET", "/admin/wireguard", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["wiresock_allowed_apps"] != expected {
		t.Fatalf("expected wiresock_allowed_apps %q, got %v", expected, body["wiresock_allowed_apps"])
	}

	endpoints, ok := body["endpoints"].([]interface{})
	if !ok {
		t.Fatalf("expected endpoints array in response")
	}
	if len(endpoints) != 0 {
		t.Fatalf("expected empty endpoints list, got %d", len(endpoints))
	}
}

func TestGetWireGuardDashboard_PrefersDBSettingOverEnv(t *testing.T) {
	setupWireGuardTestDB(t)
	app := setupWireGuardApp()

	os.Setenv("WIRESOCK_ALLOWED_APPS", "env-app.exe")
	defer os.Unsetenv("WIRESOCK_ALLOWED_APPS")

	err := database.DB.Create(&models.AppSetting{
		Key:   wireSockAllowedAppsKey,
		Value: "db-app-1.exe,db-app-2.exe",
	}).Error
	if err != nil {
		t.Fatalf("failed to seed db setting: %v", err)
	}

	req := httptest.NewRequest("GET", "/admin/wireguard", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["wiresock_allowed_apps"] != "db-app-1.exe,db-app-2.exe" {
		t.Fatalf("expected db value to override env, got %v", body["wiresock_allowed_apps"])
	}
}

func TestUpdateWireGuardSettings_PersistsAndReturnsUpdatedValue(t *testing.T) {
	setupWireGuardTestDB(t)
	app := setupWireGuardApp()

	payload := `{"wiresock_allowed_apps":"chrome.exe,discord.exe"}`
	req := httptest.NewRequest("PATCH", "/admin/wireguard", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["wiresock_allowed_apps"] != "chrome.exe,discord.exe" {
		t.Fatalf("expected updated value in response, got %v", body["wiresock_allowed_apps"])
	}

	var setting models.AppSetting
	err = database.DB.Where("key = ?", wireSockAllowedAppsKey).First(&setting).Error
	if err != nil {
		t.Fatalf("expected setting to be persisted, got error: %v", err)
	}

	if setting.Value != "chrome.exe,discord.exe" {
		t.Fatalf("expected persisted value %q, got %q", "chrome.exe,discord.exe", setting.Value)
	}
}

func TestGetWireGuardDashboard_ReturnsEndpointsForWireGuardPanel(t *testing.T) {
	setupWireGuardTestDB(t)
	app := setupWireGuardApp()

	err := database.DB.Create(&models.Endpoint{Name: "Germany", Address: "de.example.com:51820", IsActive: true}).Error
	if err != nil {
		t.Fatalf("failed to seed endpoint: %v", err)
	}

	req := httptest.NewRequest("GET", "/admin/wireguard", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	endpoints, ok := body["endpoints"].([]interface{})
	if !ok {
		t.Fatalf("expected endpoints array in response")
	}
	if len(endpoints) != 1 {
		t.Fatalf("expected 1 endpoint, got %d", len(endpoints))
	}
}
