import httpx
import os
import logging

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")

async def get_user_lang(telegram_id: int) -> str:
    """Fetch the user's saved language preference from the backend DB.
    Falls back to 'en' if anything fails."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE_URL}/users/", json={
                "telegram_id": telegram_id,
                "language": "en"  # only used if user doesn't exist yet
            })
            data = resp.json()
            lang = data.get("language", "en")
            return lang if lang in ("en", "fa") else "en"
    except Exception as e:
        logging.warning(f"Could not fetch user lang: {e}")
        return "en"
