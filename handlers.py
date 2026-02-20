from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import get_protocol_menu
import httpx
import os
import logging
from utils import get_user_lang

router = Router()
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")

@router.callback_query(F.data == "buy_menu")
async def process_buy_menu(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    text = (
        "🌟 <b>Select Your Premium VPN Protocol:</b>\n\n"
        "🌐 <b>V2Ray (Shadowsocks/Vmess/Vless/Trojan)</b>\n"
        "╰ <i>Perfect for:</i> Instagram, Telegram, YouTube, and general web browsing.\n"
        "╰ <i>Features:</i> High speed, bypasses strict firewalls.\n\n"
        "⚡️ <b>Anti-Sanction & Low Ping</b>\n"
        "╰ <i>Perfect for:</i> Competitive Gaming (Call of Duty, PUBG, Valorant) and Trading.\n"
        "╰ <i>Features:</i> Ultra-low latency, rock-solid stability."
    ) if lang == "en" else (
        "🌟 <b>پروتکل پرمیوم خود را انتخاب کنید:</b>\n\n"
        "🌐 <b>V2Ray (Shadowsocks/Vmess/Vless/Trojan)</b>\n"
        "╰ <i>مناسب برای:</i> اینستاگرام، تلگرام، یوتوب و وب‌گردی روزمره.\n"
        "╰ <i>ویژگی‌ها:</i> سرعت بالا، عبور از فیلترینگ شدید.\n\n"
        "⚡️ <b>ضد تحریم و کاهش پینگ</b>\n"
        "╰ <i>مناسب برای:</i> گیمینگ حرفه‌ای (کالاف دیوتی، پابجی) و ترید.\n"
        "╰ <i>ویژگی‌ها:</i> پینگ فوق‌العاده پایین، پایداری بالا و بدون قطعی."
    )
    
    from aiogram.types import FSInputFile
    photo = FSInputFile("assets/vpn_protocols.png")
    
    # We must delete the old text message and send a new photo message
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_protocol_menu(lang)
    )

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
            
            if not subs or not isinstance(subs, list):
                text = "You don't have any active configs." if lang == "en" else "شما هیچ کانفیگ فعالی ندارید."
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
                ])
                await callback.message.edit_text(text, reply_markup=markup)
                return
            
            text = "🔑 <b>Your Configs:</b>\n\n" if lang == "en" else "🔑 <b>سرویس‌های شما:</b>\n\n"
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            
            for index, sub in enumerate(subs, 1):
                status = sub.get("status", "unknown")
                expiry = sub.get("expiry_date", "")[:10] if sub.get("expiry_date") else "N/A"
                link = sub.get("config_link", "")
                sub_id = sub.get("ID")

                # Fix doubled URLs from old bug (e.g. "https://x.comhttps://x.com/sub/...")
                if link and link.startswith("http"):
                    idx = link.find("http", 1)
                    if idx > 0:
                        link = link[idx:]

                is_wg = link and (link.startswith("#") or "[Interface]" in link)
                
                if is_wg:
                    link_text = "👇 Tap 'Get Config' below to select location &amp; download." if lang == "en" else "👇 برای انتخاب لوکیشن و دریافت کانفیگ روی 'دریافت کانفیگ' کلیک کنید."
                    btn_text = f"🌍 Download Config #{index}" if lang == "en" else f"🌍 دریافت کانفیگ #{index}"
                    buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"get_wg_{sub_id}")])
                elif link:
                    link_text = "👇 Tap 'Get Connection Link' below." if lang == "en" else "👇 برای دریافت لینک اتصال روی دکمه زیر کلیک کنید."
                    buttons.append([InlineKeyboardButton(text=f"🔗 Get Connection Link #{index}" if lang == "en" else f"🔗 دریافت لینک اتصال #{index}", callback_data=f"get_v2ray_link_{sub_id}")])
                else:
                    link_text = "Processing..."

                plan = sub.get("plan", {})
                duration = plan.get("duration_days", "")
                data_limit = plan.get("data_limit_gb", "")
                proto_name = plan.get("server_type", "Unknown")
                
                if proto_name.lower() == "wireguard":
                    proto_display = "Low Ping (WG)" if lang == "en" else "کاهش پینگ (WG)"
                elif proto_name.lower() == "v2ray":
                    proto_display = "V2Ray"
                else:
                    proto_display = proto_name.capitalize()
                
                if duration and data_limit:
                    idx_name = f"{proto_display} - {duration} Days - {data_limit}GB" if lang == "en" else f"{proto_display} - {duration} روز - {data_limit} گیگ"
                else:
                    idx_name = f"Config {index}" if lang == "en" else f"سرویس {index}"

                if lang == "en":
                    text += f"🔹 <b>{idx_name}</b> ({status})\n📅 <b>Expires:</b> {expiry}\nℹ️ {link_text}\n\n"
                else:
                    text += f"🔹 <b>{idx_name}</b> ({status})\n📅 <b>انقضا:</b> {expiry}\nℹ️ {link_text}\n\n"
            
            buttons.append([InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")])
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            if getattr(callback.message, "photo", None):
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logging.error(f"[MyConfigs] Error for user {callback.from_user.id}: {e}")
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data.startswith("get_v2ray_link_"))
async def process_get_v2ray_link(callback: CallbackQuery):
    sub_id = callback.data.split("_")[-1]
    lang = await get_user_lang(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{callback.from_user.id}/subscriptions")
            subs = resp.json()
            
            link = ""
            for sub in subs:
                if str(sub.get("ID")) == sub_id:
                    link = sub.get("config_link", "")
                    break
            
            if not link:
                msg = "Connection link not found." if lang == "en" else "لینک اتصال یافت نشد."
                await callback.answer(msg, show_alert=True)
                return

            # Fix doubled URLs if present
            if link.startswith("http"):
                idx = link.find("http", 1)
                if idx > 0:
                    link = link[idx:]

            text = (
                f"🔗 <b>Your Connection Link:</b>\n\n"
                f"<code>{link}</code>\n\n"
                f"💡 <i>Copy the link above and import it into your V2Ray/v2rayNG app.</i>"
            ) if lang == "en" else (
                f"🔗 <b>لینک اتصال شما:</b>\n\n"
                f"<code>{link}</code>\n\n"
                f"💡 <i>لینک بالا را کپی کرده و در برنامه V2Ray/v2rayNG خود وارد کنید.</i>"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📥 Get Connections (Individual)" if lang == "en" else "📥 دریافت کانفیگ‌های مجزا", callback_data=f"get_v2ray_configs_{sub_id}")],
                [InlineKeyboardButton(text="🔙 Back to My Configs" if lang == "en" else "🔙 بازگشت به سرویس‌های من", callback_data="my_configs")]
            ])
            
            import urllib.parse
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(link)}"
            
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer_photo(photo=qr_url, caption=text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logging.error(f"[GetV2RayLink] Error for user {callback.from_user.id}: {e}")
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data.startswith("get_v2ray_configs_"))
async def process_get_v2ray_configs(callback: CallbackQuery):
    sub_id = callback.data.split("_")[-1]
    lang = await get_user_lang(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{callback.from_user.id}/subscriptions")
            subs = resp.json()
            
            link = ""
            for sub in subs:
                if str(sub.get("ID")) == sub_id:
                    link = sub.get("config_link", "")
                    break
            
            if not link:
                msg = "Connection link not found." if lang == "en" else "لینک اتصال یافت نشد."
                await callback.answer(msg, show_alert=True)
                return

            if link.startswith("http"):
                idx = link.find("http", 1)
                if idx > 0:
                    link = link[idx:]
            
            # Fetch the actual subscription content from Marzban
            sub_resp = await client.get(link)
            if sub_resp.status_code != 200:
                msg = "Failed to fetch configs from server." if lang == "en" else "خطا در دریافت کانفیگ‌ها از سرور."
                await callback.answer(msg, show_alert=True)
                return
            
            import base64
            try:
                # Subscription links are base64 encoded
                decoded_configs = base64.b64decode(sub_resp.text).decode('utf-8').strip()
            except Exception as e:
                # Fallback if not base64
                decoded_configs = sub_resp.text.strip()
            
            if not decoded_configs:
                msg = "No specific configs found in the subscription." if lang == "en" else "کانفیگ مجازی در این اشتراک یافت نشد."
                await callback.answer(msg, show_alert=True)
                return
                
            configs_list = decoded_configs.split('\n')
            
            text = "📥 <b>Your Individual Connections:</b>\n\n" if lang == "en" else "📥 <b>کانفیگ‌های مجزای شما:</b>\n\n"
            for conf in configs_list:
                if conf.strip():
                    # Identify protocol
                    proto = conf.split("://")[0].upper() if "://" in conf else "Config"
                    text += f"🔹 <b>{proto}</b>\n<code>{conf.strip()}</code>\n\n"
                    
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back to My Configs" if lang == "en" else "🔙 بازگشت به سرویس‌های من", callback_data="my_configs")]
            ])
            
            if getattr(callback.message, "photo", None):
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logging.error(f"[GetV2RayConfigs] Error for user {callback.from_user.id}: {e}")
            await callback.answer("Error parsing connections.", show_alert=True)

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
                
                caption = "✅ <b>Your Config is ready!</b>\nImport this into your <a href='https://www.wiresock.net/wiresock-secure-connect/download'>Wiresock</a> app." if lang == "en" else "✅ <b>کانفیگ شما آماده است!</b>\nاین فایل را در اپلیکیشن <a href='https://www.wiresock.net/wiresock-secure-connect/download'>Wiresock</a> ایمپورت کنید."
                await callback.message.answer_document(document=file, caption=caption, parse_mode="HTML")
                await callback.answer()
            else:
                await callback.answer("Error getting config.", show_alert=True)
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)
