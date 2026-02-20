from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import get_protocol_menu
import httpx
import os

router = Router()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1")

@router.callback_query(F.data == "buy_menu")
async def process_buy_menu(callback: CallbackQuery):
    # Depending on language (we can fetch it from DB or cache, simplified here)
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"
    
    text = "Choose the VPN Protocol:" if lang == "en" else "پروتکل VPN را انتخاب کنید:"
    await callback.message.edit_text(text, reply_markup=get_protocol_menu(lang))

@router.callback_query(F.data.startswith("select_proto_"))
async def process_protocol_selection(callback: CallbackQuery):
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"
    proto = callback.data.split("_")[-1]

    # Fetch plans from backend
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/plans?type={proto}")
            plans = resp.json()
            if not plans:
                msg = "No plans available for this protocol right now." if lang == "en" else "در حال حاضر پلنی برای این پروتکل موجود نیست."
                await callback.answer(msg, show_alert=True)
                return
            
            from keyboards import get_plans_menu
            text = f"Select a {proto} plan:" if lang == "en" else f"یک پلن {proto} انتخاب کنید:"
            await callback.message.edit_text(text, reply_markup=get_plans_menu(plans, lang))
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data.startswith("select_plan_"))
async def process_plan_selection(callback: CallbackQuery):
    plan_id = callback.data.split("_")[-1]
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"
    
    # Normally we ask for Payment Method here: Crypto OR Card
    text = "You selected a plan. How would you like to pay?" if lang == "en" else "شما یک پلن انتخاب کردید. نحوه پرداخت را مشخص کنید:"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Card to Card", callback_data=f"pay_card_{plan_id}")],
        [InlineKeyboardButton(text="🪙 Crypto (USDT)", callback_data=f"pay_crypto_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="buy_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/users/", json={
                "telegram_id": callback.from_user.id,
                "language": lang
            })
            user_data = resp.json()
            balance = user_data.get("Balance", 0.0)
            
            from keyboards import get_main_menu
            
            text = (
                f"👤 **Your Profile**\n\n"
                f"🆔 ID: `{callback.from_user.id}`\n"
                f"💰 Balance: {balance} IRR\n"
            ) if lang == "en" else (
                f"👤 **پروفایل شما**\n\n"
                f"🆔 آیدی: `{callback.from_user.id}`\n"
                f"💰 موجودی: {balance} تومان\n"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
            ])
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data == "my_configs")
async def process_my_configs(callback: CallbackQuery):
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{callback.from_user.id}/subscriptions")
            subs = resp.json()
            
            if not subs:
                text = "You don't have any active configs." if lang == "en" else "شما هیچ کانفیگ فعالی ندارید."
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
                ])
                await callback.message.edit_text(text, reply_markup=markup)
                return
            
            text = "🔑 **Your Configs:**\n\n" if lang == "en" else "🔑 **سرویس‌های شما:**\n\n"
            for sub in subs:
                status = sub.get("Status", "unknown")
                expiry = sub.get("ExpiryDate", "")[:10]
                link = sub.get("ConfigLink", "Processing...")
                
                if lang == "en":
                    text += f"🔹 **Status:** {status}\n📅 **Expires:** {expiry}\n🔗 `{link}`\n\n"
                else:
                    text += f"🔹 **وضعیت:** {status}\n📅 **انقضا:** {expiry}\n🔗 `{link}`\n\n"
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
            ])
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data == "main_menu")
async def process_main_menu_back(callback: CallbackQuery):
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"
    
    welcome_text = (
        "👋 Welcome back to the Main Menu!\n\n"
        "Please select an option below:"
    ) if lang == "en" else (
        "👋 به منوی اصلی بازگشتید!\n\n"
        "لطفا یک گزینه را انتخاب کنید:"
    )

    from keyboards import get_main_menu
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu(lang))
