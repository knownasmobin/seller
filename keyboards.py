from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(lang: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if lang == "en":
        buttons = [
            [InlineKeyboardButton(text="🛒 Buy Config", callback_data="buy_menu")],
            [InlineKeyboardButton(text="🔑 My Configs", callback_data="my_configs")],
            [InlineKeyboardButton(text="👤 Profile", callback_data="profile"), 
             InlineKeyboardButton(text="🌐 Language", callback_data="change_lang")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy_menu")],
            [InlineKeyboardButton(text="🔑 سرویس‌های من", callback_data="my_configs")],
            [InlineKeyboardButton(text="👤 پروفایل", callback_data="profile"), 
             InlineKeyboardButton(text="🌐 تغییر زبان", callback_data="change_lang")]
        ]
        
    if is_admin:
        buttons.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_protocol_menu(lang: str) -> InlineKeyboardMarkup:
    # Users first select V2Ray or WireGuard
    text_v2ray = "V2Ray (Marzban)"
    text_wg = "Anti-Sanction & Low Ping (WG)" if lang == "en" else "ضد تحریم و کاهش پینگ (WG)"
    text_back = "🔙 Back" if lang == "en" else "🔙 بازگشت"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text_v2ray, callback_data="select_proto_v2ray")],
        [InlineKeyboardButton(text=text_wg, callback_data="select_proto_wireguard")],
        [InlineKeyboardButton(text=text_back, callback_data="main_menu")]
    ])

def get_plans_menu(plans: list, lang: str) -> InlineKeyboardMarkup:
    buttons = []
    for plan in plans:
        duration = plan.get('duration_days', plan.get('DurationDays', '?'))
        data_gb = plan.get('data_limit_gb', plan.get('DataLimitGB', '?'))
        plan_id = plan.get('ID', plan.get('id', 0))
        price_irr = plan.get('price_irr', plan.get('PriceIRR', 0))
        
        price_toman = int(price_irr / 10) if isinstance(price_irr, (int, float)) else price_irr
        price_formatted_irr = f"{price_irr:,.0f}" if isinstance(price_irr, (int, float)) else price_irr
        price_formatted_toman = f"{price_toman:,.0f}" if isinstance(price_toman, int) else price_toman
        
        title = f"{duration} Days - {data_gb}GB - {price_formatted_irr} IRR" if lang == "en" else f"{duration} روز - {data_gb} گیگ - {price_formatted_toman} تومان"
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"select_plan_{plan_id}")])
    
    text_back = "🔙 Back" if lang == "en" else "🔙 بازگشت"
    buttons.append([InlineKeyboardButton(text=text_back, callback_data="buy_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
