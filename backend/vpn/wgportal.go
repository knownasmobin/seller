package vpn

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

type WgPortalClient struct {
	BaseURL string
	APIKey  string
	Client  *http.Client
}

func NewWgPortalClient(baseURL, apiKey string) *WgPortalClient {
	return &WgPortalClient{
		BaseURL: baseURL,
		APIKey:  apiKey,
		Client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// CreatePeer creates a new wireguard peer configuration
func (w *WgPortalClient) CreatePeer(username string) (string, error) {
	url := fmt.Sprintf("%s/api/peers", w.BaseURL)

	payload := map[string]interface{}{
		"name": username,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+w.APIKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := w.Client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		return "", fmt.Errorf("failed to create wg peer, status: %d", resp.StatusCode)
	}

	body, _ := ioutil.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// WG config string is usually returned in the API or can be fetched via /api/peers/{id}/config
	if config, ok := result["configuration"].(string); ok {
		return config, nil
	}

	return "", errors.New("no wireguard config found in response")
}
