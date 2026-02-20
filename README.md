# VPN Seller Bot 🚀

A high-performance modern VPN Seller system powered by a **Go Backend (Fiber)** and a **Python Telegram Bot (Aiogram)**. It seamlessly integrates with Marzban (V2Ray) and WgPortal (WireGuard) panels, handling fully automated Crypto payouts (via Oxapay) and card-to-card approval flows.

## Architecture

*   **Backend (Golang):** Handles orders, the SQLite database, Oxapay crypto Webhooks, and direct REST communication with VPN Control panels. It runs lightning fast and takes almost zero memory.
*   **Telegram Bot (Python/aiogram):** Acts as the UI client, fetching menus dynamically from the API. Supports fully bilingual (English / Farsi) inline menus.

## Setup & Deployment (Docker)

Deployment to a VPS is completely automated via Docker and `docker-compose`.

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/vpn-sell-bot.git
    cd vpn-sell-bot
    ```

2.  Copy the example environment variables:
    ```bash
    cp .env.example .env
    ```

3.  Edit `.env` and fill in your details:
    *   `BOT_TOKEN`: From BotFather
    *   `ADMIN_ID`: Your personal Telegram ID for approving card screenshots.
    *   `ADMIN_CARD_NUMBER`: Bank account to display to buyers.
    *   `OXAPAY_MERCHANT_KEY`: Your Oxapay Merchant API key for crypto automations.

4.  Start the Application:
    ```bash
    docker-compose up -d --build
    ```

## Development (Local)

*   **Backend:** `cd backend && go run main.go` runs the API on `http://localhost:3000`
*   **Bot:** `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python bot.py`
