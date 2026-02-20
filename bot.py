import asyncio
import logging
import os
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1")
bot_token = os.getenv("BOT_TOKEN")

dp = Dispatcher()

async def get_or_create_user(telegram_id: int, language: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/users/", json={
                "telegram_id": telegram_id,
                "language": language
            })
            return resp.json()
        except Exception as e:
            logging.error(f"Failed to connect to backend: {e}")
            return None

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_lang = message.from_user.language_code or "en"
    # Fallback to fa or en
    lang = "fa" if "fa" in user_lang else "en"
    
    # Sync with backend
    user_data = await get_or_create_user(message.from_user.id, lang)
    
    if not user_data:
        await message.answer("⚠️ Failed to connect to our servers right now. Please try again later.")
        return

    welcome_text = (
        "👋 Welcome to our VPN Store!\n\n"
        "Here you can buy high-speed V2Ray and WireGuard configs.\n"
        "Please select an option below:"
    ) if lang == "en" else (
        "👋 به فروشگاه VPN ما خوش آمدید!\n\n"
        "در اینجا می‌توانید کانفیگ‌های پرسرعت V2Ray و WireGuard را خریداری کنید.\n"
        "لطفا یک گزینه را انتخاب کنید:"
    )

    from keyboards import get_main_menu
    admin_id = os.getenv("ADMIN_ID")
    is_admin = False
    if admin_id and str(message.from_user.id) == admin_id:
        is_admin = True
        
    await message.answer(welcome_text, reply_markup=get_main_menu(lang, is_admin=is_admin))

async def main():
    if not bot_token:
        logging.error("BOT_TOKEN is missing in the environment variables.")
        return

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    from handlers import router as main_router
    from payment_handlers import router as payment_router
    from admin_handlers import router as admin_router
    
    dp.include_router(main_router)
    dp.include_router(payment_router)
    dp.include_router(admin_router)
    
    logging.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
