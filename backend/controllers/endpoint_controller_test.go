package controllers

import (
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"github.com/gofiber/fiber/v2"
	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
)

func setupEndpointTestDB(t *testing.T) {
	t.Helper()
	// Use a unique database path per test to avoid conflicts
	os.Setenv("DB_PATH", ":memory:")
	database.Connect()
	err := database.DB.AutoMigrate(&models.Endpoint{})
	if err != nil {
		t.Fatalf("failed to migrate test db: %v", err)
	}
	// Use Unscoped to hard delete for clean test state
	database.DB.Unscoped().Where("1 = 1").Delete(&models.Endpoint{})
}

func setupEndpointApp() *fiber.App {
	app := fiber.New()
	app.Get("/endpoints", GetEndpoints)
	app.Get("/endpoints/:id", GetEndpoint)
	app.Post("/endpoints", CreateEndpoint)
	app.Patch("/endpoints/:id", UpdateEndpoint)
	app.Delete("/endpoints/:id", DeleteEndpoint)
	return app
}

func TestGetEndpoints_ReturnsOnlyActiveEndpointsByDefault(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	// Create active and inactive endpoints
	active := models.Endpoint{Name: "Active Endpoint", Address: "active.example.com:51820", IsActive: true}
	inactive := models.Endpoint{Name: "Inactive Endpoint", Address: "inactive.example.com:51820", IsActive: false}
	if err := database.DB.Create(&active).Error; err != nil {
		t.Fatalf("failed to create active endpoint: %v", err)
	}
	// Use Select to explicitly set IsActive to false, bypassing the default
	if err := database.DB.Select("name", "address", "is_active").Create(&inactive).Error; err != nil {
		t.Fatalf("failed to create inactive endpoint: %v", err)
	}
	// Update to ensure IsActive is false (GORM default might override)
	database.DB.Model(&inactive).Update("is_active", false)

	// Verify database state
	var dbEndpoints []models.Endpoint
	database.DB.Find(&dbEndpoints)
	if len(dbEndpoints) != 2 {
		t.Fatalf("expected 2 endpoints in DB, got %d", len(dbEndpoints))
	}

	req := httptest.NewRequest("GET", "/endpoints", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var endpoints []models.Endpoint
	if err := json.NewDecoder(resp.Body).Decode(&endpoints); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if len(endpoints) != 1 {
		t.Fatalf("expected 1 active endpoint, got %d. Endpoints: %+v", len(endpoints), endpoints)
	}

	if endpoints[0].Name != "Active Endpoint" {
		t.Fatalf("expected 'Active Endpoint', got %q", endpoints[0].Name)
	}

	if !endpoints[0].IsActive {
		t.Fatalf("expected endpoint to be active")
	}
}

func TestGetEndpoints_ReturnsAllEndpointsWhenAllQueryParamIsTrue(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	// Create active and inactive endpoints
	database.DB.Create(&models.Endpoint{Name: "Active Endpoint", Address: "active.example.com:51820", IsActive: true})
	database.DB.Create(&models.Endpoint{Name: "Inactive Endpoint", Address: "inactive.example.com:51820", IsActive: false})

	req := httptest.NewRequest("GET", "/endpoints?all=true", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var endpoints []models.Endpoint
	if err := json.NewDecoder(resp.Body).Decode(&endpoints); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if len(endpoints) != 2 {
		t.Fatalf("expected 2 endpoints, got %d", len(endpoints))
	}
}

func TestGetEndpoint_ReturnsEndpointById(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	endpoint := models.Endpoint{Name: "Germany", Address: "de.example.com:51820", IsActive: true}
	database.DB.Create(&endpoint)

	req := httptest.NewRequest("GET", fmt.Sprintf("/endpoints/%d", endpoint.ID), nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var result models.Endpoint
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if result.Name != "Germany" {
		t.Fatalf("expected name 'Germany', got %q", result.Name)
	}

	if result.Address != "de.example.com:51820" {
		t.Fatalf("expected address 'de.example.com:51820', got %q", result.Address)
	}
}

func TestGetEndpoint_Returns404WhenNotFound(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	req := httptest.NewRequest("GET", "/endpoints/999", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 404 {
		t.Fatalf("expected status 404, got %d", resp.StatusCode)
	}

	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if body["error"] != "Endpoint not found" {
		t.Fatalf("expected error message 'Endpoint not found', got %v", body["error"])
	}
}

func TestCreateEndpoint_CreatesNewEndpoint(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	payload := `{"name":"Germany","address":"de.example.com:51820","is_active":true}`
	req := httptest.NewRequest("POST", "/endpoints", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 201 {
		t.Fatalf("expected status 201, got %d", resp.StatusCode)
	}

	var endpoint models.Endpoint
	if err := json.NewDecoder(resp.Body).Decode(&endpoint); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if endpoint.Name != "Germany" {
		t.Fatalf("expected name 'Germany', got %q", endpoint.Name)
	}

	if endpoint.Address != "de.example.com:51820" {
		t.Fatalf("expected address 'de.example.com:51820', got %q", endpoint.Address)
	}

	if !endpoint.IsActive {
		t.Fatalf("expected endpoint to be active")
	}

	// Verify it was saved to database
	var dbEndpoint models.Endpoint
	if err := database.DB.First(&dbEndpoint, endpoint.ID).Error; err != nil {
		t.Fatalf("expected endpoint to be saved in database: %v", err)
	}
}

func TestCreateEndpoint_Returns400ForInvalidBody(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	// Send invalid JSON that can't be parsed
	payload := `{invalid json}`
	req := httptest.NewRequest("POST", "/endpoints", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 400 {
		t.Fatalf("expected status 400, got %d", resp.StatusCode)
	}
}

func TestUpdateEndpoint_UpdatesEndpointFields(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	endpoint := models.Endpoint{Name: "Germany", Address: "de.example.com:51820", IsActive: true}
	database.DB.Create(&endpoint)

	payload := `{"name":"Germany Updated","address":"de-new.example.com:51820","is_active":false}`
	req := httptest.NewRequest("PATCH", fmt.Sprintf("/endpoints/%d", endpoint.ID), strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var result models.Endpoint
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if result.Name != "Germany Updated" {
		t.Fatalf("expected name 'Germany Updated', got %q", result.Name)
	}

	if result.Address != "de-new.example.com:51820" {
		t.Fatalf("expected address 'de-new.example.com:51820', got %q", result.Address)
	}

	if result.IsActive {
		t.Fatalf("expected endpoint to be inactive")
	}

	// Verify it was saved to database
	var dbEndpoint models.Endpoint
	database.DB.First(&dbEndpoint, endpoint.ID)
	if dbEndpoint.Name != "Germany Updated" {
		t.Fatalf("expected updated name in database, got %q", dbEndpoint.Name)
	}
}

func TestUpdateEndpoint_UpdatesPartialFields(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	endpoint := models.Endpoint{Name: "Germany", Address: "de.example.com:51820", IsActive: true}
	database.DB.Create(&endpoint)

	payload := `{"name":"Germany Updated"}`
	req := httptest.NewRequest("PATCH", fmt.Sprintf("/endpoints/%d", endpoint.ID), strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 200 {
		t.Fatalf("expected status 200, got %d", resp.StatusCode)
	}

	var result models.Endpoint
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if result.Name != "Germany Updated" {
		t.Fatalf("expected name 'Germany Updated', got %q", result.Name)
	}

	// Address should remain unchanged
	if result.Address != "de.example.com:51820" {
		t.Fatalf("expected address to remain 'de.example.com:51820', got %q", result.Address)
	}
}

func TestUpdateEndpoint_Returns404WhenNotFound(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	payload := `{"name":"Updated"}`
	req := httptest.NewRequest("PATCH", "/endpoints/999", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 404 {
		t.Fatalf("expected status 404, got %d", resp.StatusCode)
	}
}

func TestDeleteEndpoint_DeletesEndpoint(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	endpoint := models.Endpoint{Name: "Germany", Address: "de.example.com:51820", IsActive: true}
	database.DB.Create(&endpoint)

	req := httptest.NewRequest("DELETE", fmt.Sprintf("/endpoints/%d", endpoint.ID), nil)
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

	if body["message"] != "Endpoint deleted" {
		t.Fatalf("expected message 'Endpoint deleted', got %v", body["message"])
	}

	// Verify it was soft-deleted from database (should not be found with normal query)
	var dbEndpoint models.Endpoint
	if err := database.DB.First(&dbEndpoint, endpoint.ID).Error; err == nil {
		t.Fatalf("expected endpoint to be soft-deleted from database")
	}

	// Verify it exists with Unscoped (soft delete)
	var deletedEndpoint models.Endpoint
	if err := database.DB.Unscoped().First(&deletedEndpoint, endpoint.ID).Error; err != nil {
		t.Fatalf("expected endpoint to exist in database (soft deleted): %v", err)
	}
	if deletedEndpoint.DeletedAt.Time.IsZero() {
		t.Fatalf("expected endpoint to have DeletedAt set")
	}
}

func TestDeleteEndpoint_Returns404WhenNotFound(t *testing.T) {
	setupEndpointTestDB(t)
	app := setupEndpointApp()

	req := httptest.NewRequest("DELETE", "/endpoints/999", nil)
	resp, err := app.Test(req, -1)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}

	if resp.StatusCode != 404 {
		t.Fatalf("expected status 404, got %d", resp.StatusCode)
	}
}

