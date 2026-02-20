package vpn

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"time"
)

type WgPortalClient struct {
	BaseURL  string
	Username string
	Password string
	Client   *http.Client
}

func NewWgPortalClient(baseURL, username, password string) *WgPortalClient {
	return &WgPortalClient{
		BaseURL:  baseURL,
		Username: username,
		Password: password,
		Client: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// CreatePeer creates a new wireguard peer configuration via the H44Z WgPortal API
func (w *WgPortalClient) CreatePeer(username string) (string, error) {
	// 1. Get available interfaces to find the InterfaceIdentifier (usually "wg0")
	reqAuth, _ := http.NewRequest("GET", fmt.Sprintf("%s/api/v1/interface/all", w.BaseURL), nil)
	reqAuth.SetBasicAuth(w.Username, w.Password)
	resp1, err := w.Client.Do(reqAuth)
	if err != nil {
		return "", err
	}
	defer resp1.Body.Close()

	if resp1.StatusCode != 200 {
		return "", fmt.Errorf("failed to fetch interfaces, status: %d", resp1.StatusCode)
	}

	var interfaces []map[string]interface{}
	body1, _ := ioutil.ReadAll(resp1.Body)
	json.Unmarshal(body1, &interfaces)

	if len(interfaces) == 0 {
		return "", errors.New("no wireguard interfaces found in wg-portal")
	}

	interfaceID := interfaces[0]["Identifier"].(string)

	// 2. Provision the new peer
	provReq := map[string]interface{}{
		"InterfaceIdentifier": interfaceID,
		"DisplayName":         username,
	}

	provJSON, _ := json.Marshal(provReq)
	reqProv, _ := http.NewRequest("POST", fmt.Sprintf("%s/api/v1/provisioning/new-peer", w.BaseURL), bytes.NewBuffer(provJSON))
	reqProv.SetBasicAuth(w.Username, w.Password)
	reqProv.Header.Set("Content-Type", "application/json")

	resp2, err := w.Client.Do(reqProv)
	if err != nil {
		return "", err
	}
	defer resp2.Body.Close()

	if resp2.StatusCode != 200 {
		bodyErr, _ := ioutil.ReadAll(resp2.Body)
		return "", fmt.Errorf("failed to provision peer, status: %d, response: %s", resp2.StatusCode, string(bodyErr))
	}

	var peerData map[string]interface{}
	body2, _ := ioutil.ReadAll(resp2.Body)
	json.Unmarshal(body2, &peerData)

	peerPubKey, ok := peerData["Identifier"].(string)
	if !ok {
		return "", errors.New("failed to parse peer public key from provisioning response")
	}

	// 3. Fetch the configuration file for the newly created peer
	configURL := fmt.Sprintf("%s/api/v1/provisioning/data/peer-config?PeerId=%s", w.BaseURL, url.QueryEscape(peerPubKey))
	reqConf, _ := http.NewRequest("GET", configURL, nil)
	reqConf.SetBasicAuth(w.Username, w.Password)

	resp3, err := w.Client.Do(reqConf)
	if err != nil {
		return "", err
	}
	defer resp3.Body.Close()

	if resp3.StatusCode != 200 {
		return "", fmt.Errorf("failed to fetch peer config, status: %d", resp3.StatusCode)
	}

	configBytes, _ := ioutil.ReadAll(resp3.Body)
	return string(configBytes), nil
}
