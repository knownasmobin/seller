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
func (w *WgPortalClient) CreatePeer(username string, expiryDate time.Time) (string, error) {
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

	// 2.5 Update the peer with the expiry date
	if !expiryDate.IsZero() {
		peerData["ExpiresAt"] = expiryDate.Format("2006-01-02")

		updateJSON, _ := json.Marshal(peerData)
		updateURL := fmt.Sprintf("%s/api/v1/peer/by-id/%s", w.BaseURL, url.PathEscape(peerPubKey))
		reqUpdate, _ := http.NewRequest("PUT", updateURL, bytes.NewBuffer(updateJSON))
		reqUpdate.SetBasicAuth(w.Username, w.Password)
		reqUpdate.Header.Set("Content-Type", "application/json")

		respUpdate, err := w.Client.Do(reqUpdate)
		if err == nil {
			if respUpdate.StatusCode != 200 {
				bodyUpdateErr, _ := ioutil.ReadAll(respUpdate.Body)
				return "", fmt.Errorf("failed to update peer expiry, status: %d, response: %s", respUpdate.StatusCode, string(bodyUpdateErr))
			}
			respUpdate.Body.Close()
		} else {
			return "", fmt.Errorf("failed to make update peer request: %v", err)
		}
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

// GetAllPeerMetrics gets the traffic usage metrics of all peers by iterating through all users.
// Returns a map[string]int64 where the key is the peer Public Key (Identifier) and the value is the total bytes used.
func (w *WgPortalClient) GetAllPeerMetrics() (map[string]int64, error) {
	usageMap := make(map[string]int64)

	// 1. Fetch all users
	reqUsers, _ := http.NewRequest("GET", fmt.Sprintf("%s/api/v1/user/all", w.BaseURL), nil)
	reqUsers.SetBasicAuth(w.Username, w.Password)

	respUsers, err := w.Client.Do(reqUsers)
	if err != nil {
		return nil, err
	}
	defer respUsers.Body.Close()

	if respUsers.StatusCode != 200 {
		return nil, fmt.Errorf("failed to fetch users, status: %d", respUsers.StatusCode)
	}

	var users []map[string]interface{}
	bodyUsers, _ := ioutil.ReadAll(respUsers.Body)
	json.Unmarshal(bodyUsers, &users)

	// 2. Fetch metrics for each user
	for _, u := range users {
		uid, ok := u["Identifier"].(string)
		if !ok {
			continue
		}

		reqMetrics, _ := http.NewRequest("GET", fmt.Sprintf("%s/api/v1/metrics/by-user/%s", w.BaseURL, uid), nil)
		reqMetrics.SetBasicAuth(w.Username, w.Password)

		respMetrics, err := w.Client.Do(reqMetrics)
		if err != nil || respMetrics.StatusCode != 200 {
			if respMetrics != nil {
				respMetrics.Body.Close()
			}
			continue
		}

		var userMetrics map[string]interface{}
		bodyMetrics, _ := ioutil.ReadAll(respMetrics.Body)
		json.Unmarshal(bodyMetrics, &userMetrics)
		respMetrics.Body.Close()

		peerMetrics, ok := userMetrics["PeerMetrics"].([]interface{})
		if !ok {
			continue
		}

		for _, pm := range peerMetrics {
			pmMap, ok := pm.(map[string]interface{})
			if !ok {
				continue
			}

			peerID, ok := pmMap["PeerIdentifier"].(string)
			if !ok {
				continue
			}

			var bytesReceived int64
			var bytesTransmitted int64

			if br, ok := pmMap["BytesReceived"].(float64); ok {
				bytesReceived = int64(br)
			}
			if bt, ok := pmMap["BytesTransmitted"].(float64); ok {
				bytesTransmitted = int64(bt)
			}

			usageMap[peerID] = bytesReceived + bytesTransmitted
		}
	}

	return usageMap, nil
}

// DisablePeer marks a peer as disabled
func (w *WgPortalClient) DisablePeer(peerPubKey string) error {
	// 1. Fetch existing peer
	peerURL := fmt.Sprintf("%s/api/v1/peer/by-id/%s", w.BaseURL, url.PathEscape(peerPubKey))
	reqGet, _ := http.NewRequest("GET", peerURL, nil)
	reqGet.SetBasicAuth(w.Username, w.Password)

	respGet, err := w.Client.Do(reqGet)
	if err != nil {
		return err
	}
	defer respGet.Body.Close()

	if respGet.StatusCode != 200 {
		return fmt.Errorf("failed to fetch peer for disabling: %d", respGet.StatusCode)
	}

	var peerData map[string]interface{}
	bodyGet, _ := ioutil.ReadAll(respGet.Body)
	json.Unmarshal(bodyGet, &peerData)

	// 2. Modify and PUT
	peerData["Disabled"] = true
	peerData["DisabledReason"] = "Data limit reached"

	updateJSON, _ := json.Marshal(peerData)
	reqUpdate, _ := http.NewRequest("PUT", peerURL, bytes.NewBuffer(updateJSON))
	reqUpdate.SetBasicAuth(w.Username, w.Password)
	reqUpdate.Header.Set("Content-Type", "application/json")

	respUpdate, err := w.Client.Do(reqUpdate)
	if err != nil {
		return err
	}
	defer respUpdate.Body.Close()

	if respUpdate.StatusCode != 200 {
		return fmt.Errorf("failed to disable peer: %d", respUpdate.StatusCode)
	}

	return nil
}
