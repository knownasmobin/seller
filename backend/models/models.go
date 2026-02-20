package models

import (
	"time"

	"gorm.io/gorm"
)

type User struct {
	ID         uint    `gorm:"primaryKey"`
	TelegramID int64   `gorm:"uniqueIndex;not null"`
	Language   string  `gorm:"size:10;default:'fa'"`
	Balance    float64 `gorm:"default:0.0"`
	IsAdmin    bool    `gorm:"default:false"`
	CreatedAt  time.Time
	UpdatedAt  time.Time
	DeletedAt  gorm.DeletedAt `gorm:"index"`
}

type Server struct {
	ID          uint   `gorm:"primaryKey"`
	Name        string `gorm:"size:50"`
	ServerType  string `gorm:"size:20"` // "v2ray" or "wireguard"
	APIUrl      string `gorm:"size:200"`
	Credentials string `gorm:"type:text"` // JSON format (username/password or apiKey)
	IsActive    bool   `gorm:"default:true"`
	CreatedAt   time.Time
	UpdatedAt   time.Time
	DeletedAt   gorm.DeletedAt `gorm:"index"`
}

type Plan struct {
	ID           uint   `gorm:"primaryKey"`
	ServerType   string `gorm:"size:20"`
	DurationDays int
	DataLimitGB  float64
	PriceIRR     float64
	PriceUSDT    float64
	IsActive     bool `gorm:"default:true"`
	CreatedAt    time.Time
	UpdatedAt    time.Time
	DeletedAt    gorm.DeletedAt `gorm:"index"`
}

type Order struct {
	ID            uint `gorm:"primaryKey"`
	UserID        uint
	PlanID        uint
	Amount        float64
	PaymentMethod string `gorm:"size:20"`                   // "card", "crypto"
	PaymentStatus string `gorm:"size:20;default:'pending'"` // "pending", "approved", "rejected"
	ProofImageID  string `gorm:"size:200"`
	CryptoTxID    string `gorm:"size:200"`
	CreatedAt     time.Time
	UpdatedAt     time.Time
	DeletedAt     gorm.DeletedAt `gorm:"index"`
}

type Subscription struct {
	ID         uint `gorm:"primaryKey"`
	UserID     uint
	PlanID     uint
	ServerID   uint
	ConfigLink string `gorm:"type:text"`
	UUID       string `gorm:"size:100;uniqueIndex"`
	StartDate  time.Time
	ExpiryDate time.Time
	Status     string `gorm:"size:20;default:'active'"` // "active", "expired", "disabled"
	CreatedAt  time.Time
	UpdatedAt  time.Time
	DeletedAt  gorm.DeletedAt `gorm:"index"`
}
