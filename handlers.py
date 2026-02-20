from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import get_protocol_menu
import httpx
import os
from utils import get_user_lang

router = Router()
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")

@router.callback_query(F.data == "buy_menu")
async def process_buy_menu(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    text = "Choose the VPN Protocol:" if lang == "en" else "پروتکل VPN را انتخاب کنید:"
    await callback.message.edit_text(text, reply_markup=get_protocol_menu(lang))

@router.callback_query(F.data.startswith("select_proto_"))
async def process_protocol_selection(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    proto = callback.data.split("_")[-1]

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
    lang = await get_user_lang(callback.from_user.id)
    
    text = "You selected a plan. How would you like to pay?" if lang == "en" else "شما یک پلن انتخاب کردید. نحوه پرداخت را مشخص کنید:"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Card to Card" if lang == "en" else "💳 کارت به کارت", callback_data=f"pay_card_{plan_id}")],
        [InlineKeyboardButton(text="🪙 Crypto (USDT)" if lang == "en" else "🪙 کریپتو (USDT)", callback_data=f"pay_crypto_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="buy_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/users/", json={
                "telegram_id": callback.from_user.id,
                "language": lang
            })
            user_data = resp.json()
            balance = user_data.get("balance", 0.0)
            
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
    lang = await get_user_lang(callback.from_user.id)
    
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
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            
            for index, sub in enumerate(subs, 1):
                status = sub.get("status", "unknown")
                expiry = sub.get("expiry_date", "")[:10]
                link = sub.get("config_link", "Processing...")
                sub_id = sub.get("ID")
                is_wg = link.startswith("#") or "[Interface]" in link
                
                if is_wg:
                    link_text = "👇 Tap 'Get Config' below to select location & download." if lang == "en" else "👇 برای انتخاب لوکیشن و دریافت کانفیگ روی 'دریافت کانفیگ' کلیک کنید."
                    buttons.append([InlineKeyboardButton(text=f"🌍 Download Config #{index}", callback_data=f"get_wg_{sub_id}")])
                else:
                    link_text = f"`{link}`"

                if lang == "en":
                    text += f"🔹 **Config {index}** ({status})\n📅 **Expires:** {expiry}\n🔗 {link_text}\n\n"
                else:
                    text += f"🔹 **سرویس {index}** ({status})\n📅 **انقضا:** {expiry}\n🔗 {link_text}\n\n"
            
            buttons.append([InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")])
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data == "main_menu")
async def process_main_menu_back(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    welcome_text = (
        "👋 Welcome back to the Main Menu!\n\n"
        "Please select an option below:"
    ) if lang == "en" else (
        "👋 به منوی اصلی بازگشتید!\n\n"
        "لطفا یک گزینه را انتخاب کنید:"
    )

    from keyboards import get_main_menu
    admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
    is_admin = str(callback.from_user.id) in admin_ids
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu(lang, is_admin=is_admin))

@router.callback_query(F.data == "change_lang")
async def process_change_lang(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")],
        [InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="set_lang_fa")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    await callback.message.edit_text("🌐 Choose your language / زبان را انتخاب کنید:", reply_markup=markup)

@router.callback_query(F.data.startswith("set_lang_"))
async def process_set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[-1]  # "en" or "fa"
    
    # Update language in backend using the dedicated update endpoint
    async with httpx.AsyncClient() as client:
        try:
            await client.patch(f"{API_BASE_URL}/users/{callback.from_user.id}/language", json={
                "language": lang
            })
        except Exception:
            pass
    
    msg = "✅ Language set to English!" if lang == "en" else "✅ زبان به فارسی تغییر کرد!"
    await callback.answer(msg, show_alert=True)
    
    # Go back to main menu
    from keyboards import get_main_menu
    admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
    is_admin = str(callback.from_user.id) in admin_ids
    
    welcome_text = (
        "👋 Welcome back to the Main Menu!\n\n"
        "Please select an option below:"
    ) if lang == "en" else (
        "👋 به منوی اصلی بازگشتید!\n\n"
        "لطفا یک گزینه را انتخاب کنید:"
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu(lang, is_admin=is_admin))

@router.callback_query(F.data.startswith("get_wg_"))
async def process_get_wg_config(callback: CallbackQuery):
    sub_id = callback.data.split("_")[2]
    lang = await get_user_lang(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            ep_resp = await client.get(f"{API_BASE_URL}/endpoints")
            endpoints = ep_resp.json()
            
            if not endpoints:
                await callback.answer("No endpoints available." if lang == "en" else "هیچ اندپوینتی موجود نیست.", show_alert=True)
                return
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            for ep in endpoints:
                btn_text = ep.get("name", ep.get("address"))
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"dl_wg_{sub_id}_{ep.get('ID')}")])
            buttons.append([InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="my_configs")])
            
            text = "🌍 **Select a server location to download your WireGuard config:**" if lang == "en" else "🌍 **برای دریافت کانفیگ WireGuard، لوکیشن سرور را انتخاب کنید:**"
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
        except Exception:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data.startswith("dl_wg_"))
async def process_dl_wg_config(callback: CallbackQuery):
    parts = callback.data.split("_")
    sub_id = parts[2]
    ep_id = parts[3]
    lang = await get_user_lang(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{callback.from_user.id}/subscriptions/{sub_id}/wg_config?endpoint_id={ep_id}")
            if resp.status_code == 200:
                data = resp.json()
                config_text = data.get("config")
                uuid_str = data.get("uuid")
                
                from aiogram.types import BufferedInputFile
                import io
                
                conf_bytes = config_text.encode('utf-8')
                file = BufferedInputFile(conf_bytes, filename=f"wg_{uuid_str}.conf")
                
                caption = "✅ **Your Config is ready!**\nImport this into your WireGuard app." if lang == "en" else "✅ **کانفیگ شما آماده است!**\nاین فایل را در اپلیکیشن WireGuard ایمپورت کنید."
                await callback.message.answer_document(document=file, caption=caption, parse_mode="Markdown")
                await callback.answer()
            else:
                await callback.answer("Error getting config.", show_alert=True)
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)
