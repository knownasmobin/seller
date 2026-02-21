package worker

import (
	"testing"
)

func TestExtractPubKeyFromConfigLink(t *testing.T) {
	tests := []struct {
		name     string
		link     string
		expected string
	}{
		{
			name:     "Valid Link",
			link:     "http://example.com/api/v1/provisioning/data/peer-config?PeerId=somePubKey123=",
			expected: "somePubKey123=",
		},
		{
			name:     "Invalid Link missing PeerId",
			link:     "http://example.com/api/v1/provisioning/data/peer-config",
			expected: "",
		},
		{
			name:     "Empty Link",
			link:     "",
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractPubKeyFromConfigLink(tt.link)
			if got != tt.expected {
				t.Errorf("extractPubKeyFromConfigLink() = %v, want %v", got, tt.expected)
			}
		})
	}
}
