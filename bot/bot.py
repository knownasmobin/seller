import asyncio
import logging
import os
import httpx
from aiogram import Bot, Dispatcher, types, Router, F, BaseMiddleware
from aiogram.filters import CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv("../.env")
logging.basicConfig(level=logging.INFO)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1")
bot_token = os.getenv("BOT_TOKEN")

dp = Dispatcher()

class RegistrationState(StatesGroup):
    waiting_for_invite_code = State()

async def get_or_create_user(telegram_id: int, language: str, invite_code: str = ""):
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
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

auth_cache = set()
channel_verified_cache = set()

async def get_required_channel():
    """Fetch the required channel from backend"""
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/settings/required_channel")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("required_channel", "").strip()
        except Exception as e:
            logging.error(f"Failed to fetch required channel: {e}")
        return ""

async def check_channel_membership(bot: Bot, user_id: int, channel: str) -> bool:
    """Check if user is a member of the channel using Telegram API"""
    if not channel:
        return True  # No channel required
    
    try:
        # Channel can be username (e.g., @channel) or ID (e.g., -1001234567890)
        chat_id = channel
        if channel.startswith("@"):
            chat_id = channel
        else:
            # Try to parse as integer ID
            try:
                chat_id = int(channel)
            except ValueError:
                chat_id = channel
        
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        # Status can be: member, administrator, creator, left, kicked, restricted
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Failed to check channel membership for {user_id} in {channel}: {e}")
        # If bot is not admin of channel or channel doesn't exist, allow access
        # Admin should ensure bot is added to channel as admin
        return True

class ChannelVerificationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        if not isinstance(event, (types.Message, types.CallbackQuery)):
            return await handler(event, data)
        
        user = event.from_user
        if not user:
            return await handler(event, data)
        
        # Skip for admins
        admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
        if str(user.id) in admin_ids:
            return await handler(event, data)
        
        # Skip if already verified
        if user.id in channel_verified_cache:
            return await handler(event, data)
        
        # Get bot instance from data
        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)
        
        # Get required channel
        required_channel = await get_required_channel()
        if not required_channel:
            # No channel required, allow access
            return await handler(event, data)
        
        # Check membership
        is_member = await check_channel_membership(bot, user.id, required_channel)
        
        if not is_member:
            # User is not a member, show join message
            lang = user.language_code or "en"
            initial_lang = "fa" if "fa" in lang else "en"
            
            # Format channel name for display
            channel_display = required_channel if required_channel.startswith("@") else f"@{required_channel}"
            
            msg_text = (
                f"🔒 <b>Channel Membership Required</b>\n\n"
                f"🇺🇸 Please join our channel to continue using this bot:\n"
                f"📢 {channel_display}\n\n"
                f"After joining, press the button below to verify."
            ) if initial_lang == "en" else (
                f"🔒 <b>عضویت در کانال الزامی است</b>\n\n"
                f"🇮🇷 لطفاً برای ادامه استفاده از ربات، در کانال ما عضو شوید:\n"
                f"📢 {channel_display}\n\n"
                f"پس از عضویت، دکمه زیر را فشار دهید."
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            verify_button = InlineKeyboardButton(
                text="✅ Verify / تأیید" if initial_lang == "en" else "✅ تأیید",
                callback_data="verify_channel"
            )
            
            # Create join button - only if channel is a username (not numeric ID)
            buttons = []
            if required_channel.startswith("@"):
                # Username format: @channel -> https://t.me/channel
                channel_username = required_channel.lstrip("@")
                join_button = InlineKeyboardButton(
                    text=f"📢 Join Channel / عضویت در کانال" if initial_lang == "en" else f"📢 عضویت در کانال",
                    url=f"https://t.me/{channel_username}"
                )
                buttons.append([join_button])
            buttons.append([verify_button])
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            if isinstance(event, types.Message):
                await event.answer(msg_text, parse_mode=ParseMode.HTML, reply_markup=markup)
            elif isinstance(event, types.CallbackQuery):
                await event.message.answer(msg_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                await event.answer()
            return
        
        # User is a member, add to cache
        channel_verified_cache.add(user.id)
        return await handler(event, data)

class InviteMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        if not isinstance(event, (types.Message, types.CallbackQuery)):
            return await handler(event, data)
            
        user = event.from_user
        if not user:
            return await handler(event, data)
            
        if user.id in auth_cache:
            return await handler(event, data)
            
        state: FSMContext = data.get("state")
        current_state = await state.get_state() if state else None
        
        if current_state == RegistrationState.waiting_for_invite_code.state:
            return await handler(event, data)
            
        if isinstance(event, types.Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)
            
        user_lang = user.language_code or "en"
        initial_lang = "fa" if "fa" in user_lang else "en"
        
        user_data, error_data = await get_or_create_user(user.id, initial_lang)
        
        if error_data and error_data.get("error") in ["invite_code_required", "invalid_invite_code"]:
            if state:
                await state.set_state(RegistrationState.waiting_for_invite_code)
                
            msg_text = (
                "🔒 <b>Welcome! This bot is invite-only. / خوش آمدید! این ربات فقط با دعوتنامه کار می‌کند.</b>\n\n"
                "🇺🇸 Please enter your invite code to continue. If you were invited by a friend, ask them for their invite code.\n\n"
                "🇮🇷 لطفاً کد دعوت خود را وارد کنید. اگر توسط دوستتان دعوت شده‌اید، کد دعوت او را وارد کنید."
            )
            
            if isinstance(event, types.Message):
                await event.answer(msg_text, parse_mode=ParseMode.HTML)
            elif isinstance(event, types.CallbackQuery):
                await event.message.answer(msg_text, parse_mode=ParseMode.HTML)
                await event.answer()
            return
            
        if user_data:
            auth_cache.add(user.id)
            
        return await handler(event, data)

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

    auth_cache.add(message.from_user.id)

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

    auth_cache.add(message.from_user.id)
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
    
    # Apply middleware explicitly to Dispatcher and all Routers to ensure full coverage
    invite_middleware = InviteMiddleware()
    channel_middleware = ChannelVerificationMiddleware()
    
    # Apply invite middleware first, then channel verification
    dp.message.middleware(invite_middleware)
    dp.callback_query.middleware(invite_middleware)
    main_router.message.middleware(invite_middleware)
    main_router.callback_query.middleware(invite_middleware)
    payment_router.message.middleware(invite_middleware)
    payment_router.callback_query.middleware(invite_middleware)
    admin_router.message.middleware(invite_middleware)
    admin_router.callback_query.middleware(invite_middleware)
    
    # Apply channel verification middleware after invite check
    dp.message.middleware(channel_middleware)
    dp.callback_query.middleware(channel_middleware)
    main_router.message.middleware(channel_middleware)
    main_router.callback_query.middleware(channel_middleware)
    payment_router.message.middleware(channel_middleware)
    payment_router.callback_query.middleware(channel_middleware)
    admin_router.message.middleware(channel_middleware)
    admin_router.callback_query.middleware(channel_middleware)
    
    logging.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
