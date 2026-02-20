package vpn

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"time"
)

type MarzbanClient struct {
	BaseURL  string
	Username string
	Password string
	Token    string
	Client   *http.Client
}

func NewMarzbanClient(baseURL, username, password string) *MarzbanClient {
	return &MarzbanClient{
		BaseURL:  baseURL,
		Username: username,
		Password: password,
		Client: &http.Client{
			Timeout: 60 * time.Second,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
			},
		},
	}
}

// Login obtains the JWT token
func (m *MarzbanClient) Login() error {
	apiURL := fmt.Sprintf("%s/api/admin/token", m.BaseURL)

	// Marzban uses x-www-form-urlencoded for login
	formData := url.Values{}
	formData.Set("username", m.Username)
	formData.Set("password", m.Password)

	log.Printf("[Marzban] Attempting login to %s as user '%s'", apiURL, m.Username)

	req, err := http.NewRequest("POST", apiURL, bytes.NewBufferString(formData.Encode()))
	if err != nil {
		return fmt.Errorf("failed to create login request: %v", err)
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := m.Client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to connect to Marzban at %s: %v", apiURL, err)
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)

	if resp.StatusCode != 200 {
		log.Printf("[Marzban] Login failed. Status: %d, Response: %s", resp.StatusCode, string(body))
		return fmt.Errorf("marzban login failed (status %d): %s", resp.StatusCode, string(body))
	}

	var result map[string]interface{}
	json.Unmarshal(body, &result)

	if token, ok := result["access_token"].(string); ok {
		m.Token = token
		log.Printf("[Marzban] Login successful")
		return nil
	}

	return fmt.Errorf("token not found in response: %s", string(body))
}

// CreateUser creates a new VPN user in Marzban
func (m *MarzbanClient) CreateUser(username string, dataLimitGB float64, expireUnixTs int64) (string, error) {
	if m.Token == "" {
		if err := m.Login(); err != nil {
			return "", err
		}
	}

	apiURL := fmt.Sprintf("%s/api/user", m.BaseURL)

	// Convert GB to Bytes
	var dataLimit int64
	if dataLimitGB > 0 {
		dataLimit = int64(dataLimitGB * 1024 * 1024 * 1024)
	}

	payload := map[string]interface{}{
		"username":                  username,
		"status":                    "active",
		"data_limit":                dataLimit,
		"expire":                    expireUnixTs,
		"data_limit_reset_strategy": "no_reset",
		"proxies": map[string]interface{}{
			"vmess":  map[string]interface{}{},
			"trojan": map[string]interface{}{},
			"vless": map[string]interface{}{
				"flow": "",
			},
			"shadowsocks": map[string]interface{}{
				"method": "chacha20-ietf-poly1305",
			},
		},
		"inbounds": map[string]interface{}{
			"vmess":       []string{"VMess TCP", "VMess Websocket"},
			"trojan":      []string{"Trojan TCP"},
			"vless":       []string{"VLess TCP"},
			"shadowsocks": []string{"Shadowsocks TCP"},
		},
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	log.Printf("[Marzban] Creating user '%s' at %s", username, apiURL)

	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+m.Token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.Client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to connect to Marzban: %v", err)
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)

	if resp.StatusCode != 200 {
		log.Printf("[Marzban] CreateUser failed. Status: %d, Response: %s", resp.StatusCode, string(body))
		return "", fmt.Errorf("failed to create user (status %d): %s", resp.StatusCode, string(body))
	}

	log.Printf("[Marzban] CreateUser response: %s", string(body))

	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// Marzban returns subscription_url in the create response (e.g. "/sub/username/")
	if subURL, ok := result["subscription_url"].(string); ok && subURL != "" {
		log.Printf("[Marzban] User created. Subscription URL: %s", subURL)
		return subURL, nil
	}

	// Fallback: some Marzban versions return links array
	if links, ok := result["links"].([]interface{}); ok && len(links) > 0 {
		if link, ok := links[0].(string); ok {
			log.Printf("[Marzban] User created. Link: %s", link)
			return link, nil
		}
	}

	return "", fmt.Errorf("no subscription URL found in response: %s", string(body))
}
