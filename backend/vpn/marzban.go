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
			Timeout: 10 * time.Second,
		},
	}
}

// Login obtains the JWT token
func (m *MarzbanClient) Login() error {
	url := fmt.Sprintf("%s/api/admin/token", m.BaseURL)

	// Marzban uses x-www-form-urlencoded for login
	data := fmt.Sprintf("username=%s&password=%s", m.Username, m.Password)

	req, err := http.NewRequest("POST", url, bytes.NewBufferString(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := m.Client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return errors.New("failed to login to Marzban")
	}

	body, _ := ioutil.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)

	if token, ok := result["access_token"].(string); ok {
		m.Token = token
		return nil
	}

	return errors.New("token not found in response")
}

// CreateUser creates a new VPN user in Marzban
func (m *MarzbanClient) CreateUser(username string, dataLimitGB float64, expireUnixTs int64) (string, error) {
	if m.Token == "" {
		if err := m.Login(); err != nil {
			return "", err
		}
	}

	url := fmt.Sprintf("%s/api/user", m.BaseURL)

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

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
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
