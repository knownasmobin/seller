package models

import (
	"time"

	"gorm.io/gorm"
)

type User struct {
	ID         uint           `gorm:"primaryKey" json:"ID"`
	TelegramID int64          `gorm:"uniqueIndex;not null" json:"telegram_id"`
	Language   string         `gorm:"size:10;default:'fa'" json:"language"`
	Balance    float64        `gorm:"default:0.0" json:"balance"`
	IsAdmin    bool           `gorm:"default:false" json:"is_admin"`
	CreatedAt  time.Time      `json:"created_at"`
	UpdatedAt  time.Time      `json:"updated_at"`
	DeletedAt  gorm.DeletedAt `gorm:"index" json:"deleted_at"`
}

type Server struct {
	ID          uint           `gorm:"primaryKey" json:"ID"`
	Name        string         `gorm:"size:50" json:"name"`
	ServerType  string         `gorm:"size:20" json:"server_type"`
	APIUrl      string         `gorm:"size:200" json:"api_url"`
	Credentials string         `gorm:"type:text" json:"credentials"`
	IsActive    bool           `gorm:"default:true" json:"is_active"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
	DeletedAt   gorm.DeletedAt `gorm:"index" json:"deleted_at"`
}

type Plan struct {
	ID           uint           `gorm:"primaryKey" json:"ID"`
	ServerType   string         `gorm:"size:20" json:"server_type"`
	DurationDays int            `json:"duration_days"`
	DataLimitGB  float64        `json:"data_limit_gb"`
	PriceIRR     float64        `json:"price_irr"`
	PriceUSDT    float64        `json:"price_usdt"`
	IsActive     bool           `gorm:"default:true" json:"is_active"`
	CreatedAt    time.Time      `json:"created_at"`
	UpdatedAt    time.Time      `json:"updated_at"`
	DeletedAt    gorm.DeletedAt `gorm:"index" json:"deleted_at"`
}

type Order struct {
	ID            uint           `gorm:"primaryKey" json:"ID"`
	UserID        uint           `json:"user_id"`
	PlanID        uint           `json:"plan_id"`
	Amount        float64        `json:"amount"`
	PaymentMethod string         `gorm:"size:20" json:"payment_method"`
	PaymentStatus string         `gorm:"size:20;default:'pending'" json:"payment_status"`
	ProofImageID  string         `gorm:"size:200" json:"proof_image_id"`
	CryptoTxID    string         `gorm:"size:200" json:"crypto_tx_id"`
	CreatedAt     time.Time      `json:"created_at"`
	UpdatedAt     time.Time      `json:"updated_at"`
	DeletedAt     gorm.DeletedAt `gorm:"index" json:"deleted_at"`
}

type Subscription struct {
	ID         uint           `gorm:"primaryKey" json:"ID"`
	UserID     uint           `json:"user_id"`
	PlanID     uint           `json:"plan_id"`
	ServerID   uint           `json:"server_id"`
	ConfigLink string         `gorm:"type:text" json:"config_link"`
	UUID       string         `gorm:"size:100;uniqueIndex" json:"uuid"`
	StartDate  time.Time      `json:"start_date"`
	ExpiryDate time.Time      `json:"expiry_date"`
	Status     string         `gorm:"size:20;default:'active'" json:"status"`
	CreatedAt  time.Time      `json:"created_at"`
	UpdatedAt  time.Time      `json:"updated_at"`
	DeletedAt  gorm.DeletedAt `gorm:"index" json:"deleted_at"`
}
