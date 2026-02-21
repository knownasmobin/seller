from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from keyboards import get_protocol_menu
import httpx
import os
import logging
from utils import get_user_lang

router = Router()
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")

@router.callback_query(F.data == "buy_menu")
async def process_buy_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
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
            logging.info(f"Plans API response for {proto}: {resp.status_code} {resp.text}")
            plans = resp.json()
            if not plans:
                msg = "⏳ Stay Tuned!\nThere are currently no active plans for this protocol. Please check back later." if lang == "en" else "⏳ شکیبا باشید!\nدر حال حاضر پلن فعالی برای این پروتکل وجود ندارد. لطفا بعدا مراجعه کنید."
                await callback.answer(msg, show_alert=True)
                return
            
            from keyboards import get_plans_menu
            text = f"📝 **Select Your {proto} Plan:**" if lang == "en" else f"📝 **پلن {proto} خود را انتخاب کنید:**"
            markup = get_plans_menu(plans, lang)
            
            if getattr(callback.message, "photo", None):
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(text, reply_markup=markup)
            else:
                await callback.message.edit_text(text, reply_markup=markup)
        except Exception as e:
            logging.exception(f"Error in process_protocol_selection:")
            await callback.answer("Backend error.", show_alert=True)

async def show_payment_methods(message_or_callback, plan_id: str, lang: str):
    text = "💳 **Plan Selected!**\n\nHow would you like to complete your purchase?" if lang == "en" else "💳 **پلن انتخاب شد!**\n\nلطفاً روش پرداخت خود را مشخص کنید:"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Card to Card" if lang == "en" else "💳 کارت به کارت", callback_data=f"pay_card_{plan_id}")],
        [InlineKeyboardButton(text="🪙 Crypto (USDT)" if lang == "en" else "🪙 کریپتو (USDT)", callback_data=f"pay_crypto_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="buy_menu")]
    ])
    
    if hasattr(message_or_callback, "message"):
        await message_or_callback.message.edit_text(text, reply_markup=markup)
    else:
        await message_or_callback.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("select_plan_"))
async def process_plan_selection(callback: CallbackQuery):
    plan_id = callback.data.split("_")[-1]
    lang = await get_user_lang(callback.from_user.id)
    
    # Check plan protocol to figure out if we should ask for custom name
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/plans/{plan_id}")
            if resp.status_code == 200:
                plan_data = resp.json()
                proto = str(plan_data.get("server_type", "")).lower()
                
                if proto == "wireguard":
                    # Wireguard doesn't support custom config names, skip to payment
                    await show_payment_methods(callback, plan_id, lang)
                    return
        except Exception as e:
            logging.error(f"Failed to fetch plan to check protocol: {e}")

    # If V2Ray or unknown, ask for custom config name
    text = (
        "📝 **Custom Config Name (Optional)**\n\n"
        "Do you want to choose a custom name for your VPN config?\n"
        "*(Allowed: 3-32 characters, a-z, 0-9, and underscores)*"
    ) if lang == "en" else (
        "📝 **نام سفارشی کانفیگ (اختیاری)**\n\n"
        "آیا می‌خواهید یک نام دلخواه برای کانفیگ خود انتخاب کنید؟\n"
        "*(مجاز: ۳ تا ۳۲ کاراکتر، حروف انگلیسی، اعداد و خط تیره پایین _)*"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Yes, customize" if lang == "en" else "✍️ بله، انتخاب نام", callback_data=f"custom_name_{plan_id}")],
        [InlineKeyboardButton(text="⏭ No, use default" if lang == "en" else "⏭ خیر، نام پیش‌فرض", callback_data=f"skip_cname_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="buy_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data.startswith("custom_name_"))
async def process_custom_name_prompt(callback: CallbackQuery, state: FSMContext):
    plan_id = callback.data.split("_")[-1]
    lang = await get_user_lang(callback.from_user.id)
    
    from payment_handlers import PaymentState
    await state.set_state(PaymentState.waiting_for_config_name)
    await state.update_data(plan_id=plan_id)
    
    text = (
        "✏️ <b>Enter your preferred config name:</b>\n\n"
        "⚠️ <i>Rules:</i>\n"
        "- Between 3 and 32 characters\n"
        "- Only lowercase letters (a-z), numbers (0-9), and underscores (_)\n"
        "- NO spaces or special symbols."
    ) if lang == "en" else (
        "✏️ <b>نام دلخواه کانفیگ خود را وارد کنید:</b>\n\n"
        "⚠️ <i>قوانین:</i>\n"
        "- بین ۳ تا ۳۲ کاراکتر\n"
        "- فقط حروف کوچک انگلیسی (a-z)، اعداد (0-9) و خط تیره پایین (_)\n"
        "- بدون فاصله یا علائم نگارشی."
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Skip" if lang == "en" else "🔙 رد شدن", callback_data=f"skip_cname_{plan_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

import re
from payment_handlers import PaymentState

@router.message(PaymentState.waiting_for_config_name, F.text)
async def process_custom_name_input(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    data = await state.get_data()
    plan_id = data.get("plan_id")
    
    config_name = message.text.strip().lower()
    
    # Validate against Marzban rules
    if not re.match(r"^[a-z0-9_]{3,32}$", config_name):
        error_msg = (
            "❌ <b>Invalid Name!</b>\n\n"
            "Please ensure it is 3-32 characters long, and contains only a-z, 0-9, or underscores (_)."
        ) if lang == "en" else (
            "❌ <b>نام نامعتبر!</b>\n\n"
            "لطفاً مطمئن شوید طول نام ۳ تا ۳۲ کاراکتر است و فقط شامل حروف انگلیسی، اعداد یا (_) می‌باشد."
        )
        await message.answer(error_msg, parse_mode="HTML")
        return
        
    await state.update_data(config_name=config_name)
    await show_payment_methods(message, plan_id, lang)

@router.callback_query(F.data.startswith("skip_cname_"))
async def process_skip_custom_name(callback: CallbackQuery, state: FSMContext):
    plan_id = callback.data.split("_")[-1]
    lang = await get_user_lang(callback.from_user.id)
    
    # Clear config_name from state if they backtrack and skip
    await state.update_data(config_name="")
    await show_payment_methods(callback, plan_id, lang)

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
                f"👤 <b>Welcome to Your Profile</b>\n\n"
                f"🆔 <b>Invite Code:</b> <code>{callback.from_user.id}</code>\n"
                f"💰 <b>Wallet Balance:</b> {balance} IRR\n\n"
                f"💡 <i>Give your invite code or link to your friends so they can join!</i>"
            ) if lang == "en" else (
                f"👤 <b>پروفایل کاربری شما</b>\n\n"
                f"🆔 <b>کد دعوت شما:</b> <code>{callback.from_user.id}</code>\n"
                f"💰 <b>موجودی کیف پول:</b> {balance} تومان\n\n"
                f"💡 <i>کد دعوت یا لینک ثبت‌نام را به دوستانتان بدهید تا بتوانند در ربات ثبت‌نام کنند!</i>"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
            ])
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data == "invite_friend")
async def process_invite_friend(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    bot_info = await callback.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    text = (
        f"🎁 <b>Invite Your Friends!</b>\n\n"
        f"Send the link below to your friends. They can also manually enter your invite code during registration.\n\n"
        f"🔗 <b>Your Invite Link:</b>\n{invite_link}\n\n"
        f"🆔 <b>Your Invite Code:</b> <code>{callback.from_user.id}</code>"
    ) if lang == "en" else (
        f"🎁 <b>دعوت از دوستان!</b>\n\n"
        f"لینک زیر را برای دوستان خود ارسال کنید. آنها همچنین می‌توانند کد دعوت شما را به صورت دستی هنگام ثبت‌نام وارد کنند.\n\n"
        f"🔗 <b>لینک دعوت شما:</b>\n{invite_link}\n\n"
        f"🆔 <b>کد دعوت شما:</b> <code>{callback.from_user.id}</code>"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "my_configs")
async def process_my_configs(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{callback.from_user.id}/subscriptions")
            subs = resp.json()
            
            if not subs or not isinstance(subs, list):
                text = "📭 <b>No Active Subscriptions</b>\n\nYou don't have any active configs at the moment. Return to the main menu to purchase one!" if lang == "en" else "📭 <b>سرویس فعالی ندارید</b>\n\nشما در حال حاضر هیچ کانفیگ فعالی ندارید. برای خرید از منوی اصلی اقدام کنید!"
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="main_menu")]
                ])
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
                return
            
            text = "📦 <b>Your Active Subscriptions:</b>\n\n" if lang == "en" else "📦 <b>سرویس‌های فعال شما:</b>\n\n"
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
                    link_text = "📥 <i>Tap the button below to select your desired location.</i>" if lang == "en" else "📥 <i>برای انتخاب لوکیشن و دریافت کانفیگ روی دکمه زیر کلیک کنید.</i>"
                    btn_text = f"🌍 Download Config #{index}" if lang == "en" else f"🌍 دریافت کانفیگ #{index}"
                    buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"get_wg_{sub_id}")])
                elif link:
                    link_text = "🔗 <i>Tap the button below to view your connection details.</i>" if lang == "en" else "🔗 <i>برای دریافت لینک اتصال روی دکمه زیر کلیک کنید.</i>"
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

                config_name = sub.get("uuid", "")
                name_line = f"📛 <code>{config_name}</code>\n" if config_name else ""

                if lang == "en":
                    text += f"{name_line}💎 <b>{idx_name}</b>\n╰ <i>Status:</i> {status}\n╰ <i>Expires:</i> {expiry}\n{link_text}\n\n"
                else:
                    text += f"{name_line}💎 <b>{idx_name}</b>\n╰ <i>وضعیت:</i> {status}\n╰ <i>انقضا:</i> {expiry}\n{link_text}\n\n"
            
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
                f"🔗 <b>Your Premium Subscription Link</b>\n\n"
                f"<code>{link}</code>\n\n"
                f"💡 <i>Copy the link above and import it into your preferred V2Ray client (e.g. v2rayNG, V2RayN, Shadowrocket).</i>"
            ) if lang == "en" else (
                f"🔗 <b>لینک اشتراک پرمیوم شما</b>\n\n"
                f"<code>{link}</code>\n\n"
                f"💡 <i>لینک بالا را کپی کرده و در برنامه V2Ray خود (مانند v2rayNG یا Shadowrocket) وارد کنید.</i>"
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
async def process_main_menu_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)
    
    welcome_text = (
        "👋 <b>Welcome to the Main Menu!</b>\n\n"
        "Select an option below to get started:"
    ) if lang == "en" else (
        "👋 <b>به منوی اصلی خوش آمدید!</b>\n\n"
        "جهت شروع، یکی از گزینه‌های زیر را انتخاب کنید:"
    )

    from keyboards import get_main_menu
    admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
    is_admin = str(callback.from_user.id) in admin_ids
    
    markup = get_main_menu(lang, is_admin=is_admin)
    if getattr(callback.message, "photo", None):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(welcome_text, reply_markup=markup)
    else:
        await callback.message.edit_text(welcome_text, reply_markup=markup)

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
        "👋 <b>Welcome to the Main Menu!</b>\n\n"
        "Select an option below to get started:"
    ) if lang == "en" else (
        "👋 <b>به منوی اصلی خوش آمدید!</b>\n\n"
        "جهت شروع، یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    await callback.message.edit_text(welcome_text, parse_mode="HTML", reply_markup=get_main_menu(lang, is_admin=is_admin))

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
            
            text = "🌍 <b>Select a Server Location</b>\n\nChoose a location below to download your WireGuard configuration:" if lang == "en" else "🌍 <b>لوکیشن سرور را انتخاب کنید</b>\n\nبرای دریافت کانفیگ WireGuard، یکی از لوکیشن‌های زیر را انتخاب کنید:"
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
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

# --- Support System ---
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

class SupportState(StatesGroup):
    waiting_for_message = State()

@router.callback_query(F.data == "support_menu")
async def process_support_menu(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    text = (
        "🎧 <b>Contact Support</b>\n\n"
        "Please type your message below. Our admin team will get back to you here shortly."
    ) if lang == "en" else (
        "🎧 <b>ارتباط با پشتیبانی</b>\n\n"
        "لطفا پیام خود را در زیر بنویسید. تیم پشتیبانی ما به زودی در همینجا پاسخ خواهند داد."
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Cancel" if lang == "en" else "🔙 انصراف", callback_data="main_menu")]
    ])
    
    if getattr(callback.message, "photo", None):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
        
    await state.set_state(SupportState.waiting_for_message)

@router.message(SupportState.waiting_for_message)
async def process_support_message(message: Message, state: FSMContext, bot):
    lang = await get_user_lang(message.from_user.id)
    user_msg = message.text
    
    admin_ids = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
    if not admin_ids:
        await message.answer("⚠️ Support system is currently unavailable.")
        await state.clear()
        return

    # Fetch user's active subscriptions to include in the ticket
    active_plans_text = "<i>No active subscriptions found.</i>"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{message.from_user.id}/subscriptions")
            if resp.status_code == 200:
                subs = resp.json()
                active_subs = [s for s in subs if s.get("status") == "active"]
                if active_subs:
                    plan_details = []
                    for idx, sub in enumerate(active_subs, 1):
                        plan_name = sub.get("plan", {}).get("name", "Unknown Plan")
                        proto = sub.get("plan", {}).get("protocol", "N/A")
                        plan_details.append(f"  └ {idx}. <b>{plan_name}</b> ({proto})")
                    active_plans_text = "\n".join(plan_details)
        except Exception as e:
            logging.error(f"Error fetching subs for support ticket: {e}")
            active_plans_text = "<i>Error retrieving subscriptions.</i>"

    admin_text = (
        f"📩 <b>New Support Ticket</b>\n"
        f"👤 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
        f"🗣 <b>Username:</b> @{message.from_user.username or 'No Username'}\n\n"
        f"📦 <b>Active Plans:</b>\n{active_plans_text}\n\n"
        f"<b>Message:</b>\n{user_msg}\n\n"
        f"<i>Reply directly to this user's message using the bot to answer them.</i>"
    )

    success = False
    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            success = True
        except Exception as e:
            logging.error(f"Failed to forward support message to {admin_id}: {e}")

    if success:
        reply_text = (
            "✅ <b>Message Sent!</b>\n\n"
            "Your message has been forwarded to our support team. We will reply as soon as possible."
        ) if lang == "en" else (
            "✅ <b>پیام ارسال شد!</b>\n\n"
            "پیام شما به تیم پشتیبانی ارسال گردید. به زودی به شما پاسخ خواهیم داد."
        )
    else:
        reply_text = "❌ Error sending message. Please try again later." if lang == "en" else "❌ خطا در ارسال پیام. لطفا بعدا تلاش کنید."

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from keyboards import get_main_menu
    is_admin = str(message.from_user.id) in admin_ids
    markup = get_main_menu(lang, is_admin=is_admin)
    
    await message.answer(reply_text, parse_mode="HTML", reply_markup=markup)
    await state.clear()
