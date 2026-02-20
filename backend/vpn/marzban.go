package vpn

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"errors"
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
			Timeout: 30 * time.Second,
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
		"username":   username,
		"proxies":    map[string]interface{}{"vless": map[string]interface{}{}, "vmess": map[string]interface{}{}},
		"data_limit": dataLimit,
		"expire":     expireUnixTs,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+m.Token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.Client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("failed to create user, status: %d", resp.StatusCode)
	}

	body, _ := ioutil.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// In Marzban, links are usually returned in the response
	if links, ok := result["links"].([]interface{}); ok && len(links) > 0 {
		return links[0].(string), nil
	}

	return "", errors.New("no subscription links found")
}
