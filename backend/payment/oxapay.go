package payment

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

type OxapayClient struct {
	MerchantKey string
	Client      *http.Client
}

func NewOxapayClient(merchantKey string) *OxapayClient {
	return &OxapayClient{
		MerchantKey: merchantKey,
		Client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// CreateInvoice generates a payment link for the given amount (in USDT)
func (o *OxapayClient) CreateInvoice(amount float64, orderID string, email string) (string, error) {
	url := "https://api.oxapay.com/merchants/request"

	payload := map[string]interface{}{
		"merchant":    o.MerchantKey,
		"amount":      amount,
		"currency":    "USDT",
		"orderId":     orderID,
		"email":       email,
		"description": fmt.Sprintf("Payment for Order %s", orderID),
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := o.Client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("failed to create oxapay invoice, status: %d", resp.StatusCode)
	}

	body, _ := ioutil.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// Oxapay returns result=1 for success and payLink contains the URL
	if res, ok := result["result"].(float64); ok && res == 100 {
		if payLink, ok := result["payLink"].(string); ok {
			return payLink, nil
		}
	}

	errorMsg := "unknown error"
	if msg, ok := result["message"].(string); ok {
		errorMsg = msg
	}

	return "", fmt.Errorf("oxapay error: %s", errorMsg)
}
