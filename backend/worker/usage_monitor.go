package worker

import (
	"encoding/json"
	"log"
	"strings"
	"time"

	"github.com/username/sell-bot-backend/database"
	"github.com/username/sell-bot-backend/models"
	"github.com/username/sell-bot-backend/vpn"
)

// StartUsageMonitor runs a background worker to check WG usage across all servers.
func StartUsageMonitor() {
	// Run every hour
	ticker := time.NewTicker(time.Duration(1) * time.Hour)
	go func() {
		// Run immediately on boot
		log.Println("[UsageMonitor] Starting initial WgPortal usage check...")
		checkWgUsage()

		for range ticker.C {
			log.Println("[UsageMonitor] Running routine WgPortal usage check...")
			checkWgUsage()
		}
	}()
}

func checkWgUsage() {
	// Only fetch active wireguard subscriptions
	var subscriptions []models.Subscription
	if err := database.DB.Preload("Plan").Where("status = ?", "active").Find(&subscriptions).Error; err != nil {
		log.Printf("[UsageMonitor] Failed to fetch active subscriptions: %v", err)
		return
	}

	// Group subscriptions by ServerID
	subsByServer := make(map[uint][]models.Subscription)
	for _, sub := range subscriptions {
		if sub.Plan.ServerType == "wireguard" {
			subsByServer[sub.ServerID] = append(subsByServer[sub.ServerID], sub)
		}
	}

	for serverID, subs := range subsByServer {
		var server models.Server
		if err := database.DB.First(&server, serverID).Error; err != nil {
			log.Printf("[UsageMonitor] Server %d not found for active subs", serverID)
			continue
		}

		var creds map[string]string
		if err := json.Unmarshal([]byte(server.Credentials), &creds); err != nil {
			log.Printf("[UsageMonitor] Invalid credentials for Server %d", serverID)
			continue
		}

		wgUser := creds["username"]
		wgPass := creds["password"]
		client := vpn.NewWgPortalClient(server.APIUrl, wgUser, wgPass)

		// Fetch all peer metrics at once for this server
		usageMap, err := client.GetAllPeerMetrics()
		if err != nil {
			log.Printf("[UsageMonitor] Failed to fetch WG metrics for server %d (%s): %v", serverID, server.Name, err)
			continue
		}

		// Check each subscription on this server against the usage map
		for _, sub := range subs {
			// Extract identifier from the config link or peer config mapping.
			// Currently, the payment_controller maps the config name / username to `sub.UUID`,
			// which matches `wg_user_{tid}_{oid}`. However, WgPortal `peerPubKey` (Identifier)
			// is what GetAllPeerMetrics keys by. Let's see if we can use the Name/DisplayName mapping
			// if the config link doesn't contain the public key.

			// WgPortal config links look like: .../api/v1/provisioning/data/peer-config?PeerId=PUBKEY
			// We can extract the PeerId (public key) from `sub.ConfigLink` to find it in the metrics.
			pubKey := extractPubKeyFromConfigLink(sub.ConfigLink)
			if pubKey == "" {
				continue
			}

			usedBytes, exists := usageMap[pubKey]
			if !exists {
				// Peer might be deleted or have 0 metrics
				continue
			}

			// Plan limit in bytes
			limitBytes := int64(sub.Plan.DataLimitGB * 1024 * 1024 * 1024)

			if limitBytes > 0 && usedBytes >= limitBytes {
				log.Printf("[UsageMonitor] UUID %s (Peer %s) exceeded limit! Used: %d bytes, Limit: %d bytes. Disabling...",
					sub.UUID, pubKey, usedBytes, limitBytes)

				if err := client.DisablePeer(pubKey); err == nil {
					// Update Database status
					sub.Status = "limit_reached"
					database.DB.Save(&sub)

					// Optionally notify the user via Telegram here (future improvement)
				} else {
					log.Printf("[UsageMonitor] Failed to disable peer %s: %v", pubKey, err)
				}
			}
		}
	}
}

// extractPubKeyFromConfigLink extracts the public key from the WgPortal config URL.
// Example: http://1.2.3.4:8080/api/v1/provisioning/data/peer-config?PeerId=o2k2o...
func extractPubKeyFromConfigLink(link string) string {
	parts := strings.Split(link, "PeerId=")
	if len(parts) == 2 {
		return parts[1]
	}
	// Fallback if the link is actually just the public key or another format
	return ""
}
