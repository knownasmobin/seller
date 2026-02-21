import asyncio
import logging
import os
import httpx
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1")
bot_token = os.getenv("BOT_TOKEN")

dp = Dispatcher()

class RegistrationState(StatesGroup):
    waiting_for_invite_code = State()

async def get_or_create_user(telegram_id: int, language: str, invite_code: str = ""):
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "telegram_id": telegram_id,
                "language": language,
                "invite_code": invite_code
            }
            resp = await client.post(f"{API_BASE_URL}/users/", json=payload)
            if resp.status_code == 200:
                return resp.json(), None
            else:
                return None, resp.json()
        except Exception as e:
            logging.error(f"Failed to connect to backend: {e}")
            return None, {"error": "connection_failed"}

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    
    user_lang = message.from_user.language_code or "en"
    # Use Telegram locale only as initial default for new users
    initial_lang = "fa" if "fa" in user_lang else "en"
    
    # Extract invite code if provided via deep link (e.g., /start 123456)
    invite_code = command.args.strip() if command.args else ""

    # Sync with backend - returns saved language for existing users
    user_data, error_data = await get_or_create_user(message.from_user.id, initial_lang, invite_code)
    
    if error_data and error_data.get("error") in ["invite_code_required", "invalid_invite_code"]:
        await state.set_state(RegistrationState.waiting_for_invite_code)
        msg_text = (
            "🔒 <b>Welcome! This bot is invite-only. / خوش آمدید! این ربات فقط با دعوتنامه کار می‌کند.</b>\n\n"
            "🇺🇸 Please enter your invite code to continue. If you were invited by a friend, ask them for their invite code.\n\n"
            "🇮🇷 لطفاً کد دعوت خود را وارد کنید. اگر توسط دوستتان دعوت شده‌اید، کد دعوت او را وارد کنید."
        )
        await message.answer(msg_text, parse_mode=ParseMode.HTML)
        return

    if not user_data:
        await message.answer("⚠️ Failed to connect to our servers right now. Please try again later.")
        return

    # Use the language from DB (respects user's choice)
    lang = user_data.get("language", initial_lang)

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
    admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
    is_admin = str(message.from_user.id) in admin_ids
        
    await message.answer(welcome_text, reply_markup=get_main_menu(lang, is_admin=is_admin))

@dp.message(RegistrationState.waiting_for_invite_code, F.text)
async def process_invite_code(message: types.Message, state: FSMContext):
    invite_code = message.text.strip()
    user_lang = message.from_user.language_code or "en"
    initial_lang = "fa" if "fa" in user_lang else "en"
    
    user_data, error_data = await get_or_create_user(message.from_user.id, initial_lang, invite_code)
    
    if error_data and error_data.get("error") == "invalid_invite_code":
        err_msg = "❌ Invalid invite code. Please try again." if initial_lang == "en" else "❌ کد دعوت نامعتبر است. لطفاً دوباره تلاش کنید."
        await message.answer(err_msg)
        return

    if not user_data:
        await message.answer("⚠️ Failed to connect to our servers right now. Please try again later.")
        return

    await state.clear()
    
    from keyboards import get_main_menu
    lang = user_data.get("language", initial_lang)
    admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
    is_admin = str(message.from_user.id) in admin_ids
    
    success_text = "✅ <b>Registration Successful!</b>\n\nWelcome to our VPN Store. Please select an option below:" if lang == "en" else "✅ <b>ثبت‌نام با موفقیت انجام شد!</b>\n\nبه فروشگاه VPN ما خوش آمدید. لطفا یک گزینه را انتخاب کنید:"
    await message.answer(success_text, reply_markup=get_main_menu(lang, is_admin=is_admin), parse_mode=ParseMode.HTML)

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
