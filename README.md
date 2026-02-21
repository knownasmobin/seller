# VPN Seller Bot 🚀

[![CI/CD Pipeline](https://github.com/knownasmobin/seller/actions/workflows/ci.yml/badge.svg)](https://github.com/knownasmobin/seller/actions/workflows/ci.yml)

A high-performance modern VPN Seller system powered by a **Go Backend (Fiber)**, a **Python Telegram Bot (Aiogram)**, and a **React Frontend Dashboard**. It seamlessly integrates with Marzban (V2Ray) and WgPortal (WireGuard) panels, handling fully automated Crypto payouts (via Oxapay) and card-to-card approval flows.

`![Bot Interface Screenshot](./assets/bot_screenshot.png)`

## 🌟 Key Bot Features
- **Fully Automated Provisioning**: Secure integrations directly create V2Ray/WireGuard peers and deliver configurations to users instantly after payment is confirmed.
- **Crypto & Card Processing**: Native support for the Oxapay crypto gateway, as well as a manual card-to-card transfer flow with receipt screenshot validation.
- **Invite-Only & Referrals**: Capable of running in an invite-only mode, with comprehensive referral tracking and rewards.
- **Bilingual Interface**: The bot dynamically supports both English and Persian (Farsi) menus based on user preference.
- **In-App Admin Panel**: Admins can approve/reject manual payments, create or disable VPN plans, and manage endpoints directly from Telegram without needing the web dashboard.

## 🏗 Architecture
The system employs a strict 3-tier architecture:
1. **/backend (Golang/Fiber)**: Extremely fast REST API utilizing an SQLite database. It acts as the central hub—processing Telegram callbacks, enforcing periodic WireGuard data usage limits via background cron jobs, and proxying requests to external VPN Panels.
2. **/bot (Python/Aiogram)**: The Telegram bot using `aiogram` v3. It is entirely detached from the database, acting purely as a UI client by making HTTP requests to the Golang Backend.
3. **/frontend (React)**: A modern administrative dashboard built with Vite + React + Tailwind CSS to manage users, plans, and metrics graphically.

`![Admin Dashboard Screenshot](./assets/dashboard_screenshot.png)`

## 🚀 Setup & Deployment (Docker)

Deployment to a VPS is completely automated via Docker and `docker-compose`.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/knownasmobin/seller.git
   cd seller
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your details:
   - `BOT_TOKEN`: Your Telegram Bot API token (from @BotFather).
   - `ADMIN_ID`: Your personal Telegram ID (or a comma-separated list of admins).
   - `ADMIN_CARD_NUMBER`: Bank account to display to buyers choosing manual payment.
   - `OXAPAY_MERCHANT_KEY`: Your Oxapay Merchant API key for crypto automations.
   - VPN Panel URLs/Credentials (Marzban & WgPortal).

3. **Start the Application:**
   ```bash
   docker-compose up -d --build
   ```
   This will boot the backend API on port `3000`, the frontend proxy on port `8085`, and the Telegram bot container.

## 💻 Local Development

If you wish to run the services manually without Docker:

*   **Backend:** 
    ```bash
    cd backend
    go mod tidy
    go run main.go
    ```
*   **Telegram Bot:** 
    ```bash
    cd bot
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python bot.py
    ```
*   **React Frontend:** 
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## 🧪 Testing

Comprehensive test suites are provided to ensure the stability of the project.

### Running Go Backend Tests
Includes unit tests with local SQLite mocking and integration tests mimicking the API servers:
```bash
cd backend
go test ./...
```

### Running Python Bot Tests
Built with `pytest` and `unittest.mock.AsyncMock` to test the Telegram handlers offline:
```bash
cd bot
python -m pytest tests/
```
