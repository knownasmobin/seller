import httpx
import os
import logging

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")

USER_LANG_CACHE = {}

async def get_user_lang(telegram_id: int) -> str:
    """Fetch the user's saved language preference from the backend DB.
    Falls back to 'en' if anything fails."""
    if telegram_id in USER_LANG_CACHE:
        return USER_LANG_CACHE[telegram_id]
        
    try:
        async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
            resp = await client.post(f"{API_BASE_URL}/users/", json={
                "telegram_id": telegram_id,
                "language": "en"  # only used if user doesn't exist yet
            })
            data = resp.json()
            lang = data.get("language", "en")
            final_lang = lang if lang in ("en", "fa") else "en"
            USER_LANG_CACHE[telegram_id] = final_lang
            return final_lang
    except Exception as e:
        logging.warning(f"Could not fetch user lang: {e}")
        return "en"

def set_user_cached_lang(telegram_id: int, lang: str):
    USER_LANG_CACHE[telegram_id] = lang
