from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(lang: str) -> InlineKeyboardMarkup:
    if lang == "en":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Buy Config", callback_data="buy_menu")],
            [InlineKeyboardButton(text="🔑 My Configs", callback_data="my_configs")],
            [InlineKeyboardButton(text="👤 Profile", callback_data="profile"), 
             InlineKeyboardButton(text="🌐 Language", callback_data="change_lang")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy_menu")],
            [InlineKeyboardButton(text="🔑 سرویس‌های من", callback_data="my_configs")],
            [InlineKeyboardButton(text="👤 پروفایل", callback_data="profile"), 
             InlineKeyboardButton(text="🌐 تغییر زبان", callback_data="change_lang")]
        ])

def get_protocol_menu(lang: str) -> InlineKeyboardMarkup:
    # Users first select V2Ray or WireGuard
    text_v2ray = "V2Ray (Marzban)"
    text_wg = "WireGuard"
    text_back = "🔙 Back" if lang == "en" else "🔙 بازگشت"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text_v2ray, callback_data="select_proto_v2ray")],
        [InlineKeyboardButton(text=text_wg, callback_data="select_proto_wireguard")],
        [InlineKeyboardButton(text=text_back, callback_data="main_menu")]
    ])

def get_plans_menu(plans: list, lang: str) -> InlineKeyboardMarkup:
    buttons = []
    for plan in plans:
        # e.g., plan = {"ID": 1, "DurationDays": 30, "DataLimitGB": 50, "PriceIRR": 100000, "PriceUSDT": 2.5}
        title = f"{plan['DurationDays']} Days - {plan['DataLimitGB']}GB" if lang == "en" else f"{plan['DurationDays']} روز - {plan['DataLimitGB']} گیگ"
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"select_plan_{plan['ID']}")])
    
    text_back = "🔙 Back" if lang == "en" else "🔙 بازگشت"
    buttons.append([InlineKeyboardButton(text=text_back, callback_data="buy_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
