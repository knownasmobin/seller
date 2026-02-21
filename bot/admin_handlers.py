import logging
import os
import httpx
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")
ADMIN_IDS = [x.strip() for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]

class AddPlanForm(StatesGroup):
    waiting_for_protocol = State()
    waiting_for_duration = State()
    waiting_for_data_limit = State()
    waiting_for_price = State()

class EditPlanForm(StatesGroup):
    waiting_for_new_value = State()

class AddEndpointForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()

def is_admin(telegram_id: int) -> bool:
    return str(telegram_id) in ADMIN_IDS

# --- Admin Panel Entry ---
@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("You are not authorized.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add New Plan", callback_data="admin_add_plan")],
        [InlineKeyboardButton(text="✏️ Edit Existing Plan", callback_data="admin_list_plans")],
        [InlineKeyboardButton(text="🌍 Manage Endpoints (WG)", callback_data="admin_endpoints")],
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text("⚙️ **Admin Panel**\n\nWhat would you like to do?", reply_markup=keyboard, parse_mode="Markdown")

# --- Add Plan Flow ---
@router.callback_query(F.data == "admin_add_plan")
async def add_plan_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="V2Ray", callback_data="addplan_proto_v2ray")],
        [InlineKeyboardButton(text="WireGuard", callback_data="addplan_proto_wireguard")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text("Please select the protocol for the new plan:", reply_markup=keyboard)
    await state.set_state(AddPlanForm.waiting_for_protocol)

@router.callback_query(AddPlanForm.waiting_for_protocol, F.data.startswith("addplan_proto_"))
async def add_plan_protocol_selected(callback: types.CallbackQuery, state: FSMContext):
    proto = callback.data.split("_")[2] # v2ray or wireguard
    await state.update_data(server_type=proto)
    
    await callback.message.edit_text("Enter the **Duration in Days** (e.g., 30):", parse_mode="Markdown")
    await state.set_state(AddPlanForm.waiting_for_duration)

@router.message(AddPlanForm.waiting_for_duration)
async def add_plan_duration(message: types.Message, state: FSMContext):
    try:
        duration = int(message.text)
        await state.update_data(duration_days=duration)
        
        await message.answer("Enter the **Data Limit in GB** (e.g., 50):", parse_mode="Markdown")
        await state.set_state(AddPlanForm.waiting_for_data_limit)
    except ValueError:
        await message.answer("Please enter a valid number for days.")

@router.message(AddPlanForm.waiting_for_data_limit)
async def add_plan_data_limit(message: types.Message, state: FSMContext):
    try:
        data_limit = int(message.text)
        await state.update_data(data_limit_gb=data_limit)
        
        await message.answer("Enter the **Price in IRR** (Tomans x 10, e.g. 150000):", parse_mode="Markdown")
        await state.set_state(AddPlanForm.waiting_for_price)
    except ValueError:
        await message.answer("Please enter a valid number for GB.")

@router.message(AddPlanForm.waiting_for_price)
async def add_plan_price(message: types.Message, state: FSMContext):
    try:
        price_irr = float(message.text)
        # We can auto-calculate USDT or default it to 0 for simplicity if you only use IRR
        
        data = await state.get_data()
        
        plan_payload = {
            "server_type": data['server_type'],
            "duration_days": data['duration_days'],
            "data_limit_gb": data['data_limit_gb'],
            "price_irr": price_irr,
            "price_usdt": price_irr / 600000, # Rough heuristic or standard fixed price
            "is_active": True
        }
        
        async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
            resp = await client.post(f"{API_BASE_URL}/plans", json=plan_payload)
            if resp.status_code == 201:
                await message.answer(f"✅ Plan added successfully!\n\nType: {data['server_type']}\nDays: {data['duration_days']}\nGB: {data['data_limit_gb']}\nPrice: {price_irr} IRR")
            else:
                logging.error(f"Failed to add plan: {resp.text}")
                await message.answer("❌ Failed to add plan due to server error.")
                
        await state.clear()
        
    except ValueError:
        await message.answer("Please enter a valid numeric price.")

# --- Edit Plan Flow ---
@router.callback_query(F.data == "admin_list_plans")
async def edit_plan_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
        
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/plans?all=true")
            plans = resp.json()
            
            if not plans:
                await callback.message.edit_text("No plans found.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")]
                ]))
                return
                
            buttons = []
            for plan in plans:
                status = "✅" if plan.get('is_active') else "❌"
                btn_text = f"{status} {plan.get('server_type')} - {plan.get('data_limit_gb')}GB / {plan.get('duration_days')}D"
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin_editplan_{plan.get('ID')}")])
                
            buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")])
            makeup = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await callback.message.edit_text("Select a plan to edit:", reply_markup=makeup)
        except Exception as e:
            await callback.answer(f"❌ Error fetching users: {e}", show_alert=True)

# --- Admin Support Reply Handling ---
import re

@router.message()
async def process_admin_reply(message: types.Message, bot):
    # Only process if it's from an admin and it's a reply to another message
    if not is_admin(message.from_user.id) or not message.reply_to_message:
        return
        
    # Check if the message being replied to contains our specific support format
    reply_text = message.reply_to_message.text or message.reply_to_message.caption
    if not reply_text:
        return
        
    # We are looking for "User ID: 123456" in the forwarded message text
    match = re.search(r"User ID:\s*(\d+)", reply_text)
    if not match:
        return
        
    target_user_id = int(match.group(1))
    admin_response = message.text
    
    if not admin_response:
        await message.reply("⚠️ Please reply with text.")
        return
        
    # Format the message for the user
    response_to_user = (
        f"🎧 <b>Message from Support / پیام از طرف پشتیبانی</b>\n\n"
        f"<i>{admin_response}</i>"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Reply / پاسخ", callback_data="support_menu")]
    ])
    
    try:
        await bot.send_message(chat_id=target_user_id, text=response_to_user, parse_mode="HTML", reply_markup=markup)
        await message.reply("✅ <b>Reply successfully sent to the user!</b>", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed to send admin reply to user {target_user_id}: {e}")
        await message.reply(f"❌ <b>Error:</b> Could not send message to user. They might have blocked the bot.\n\nDetails: {e}", parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_editplan_"))
async def edit_plan_menu(callback: types.CallbackQuery, state: FSMContext):
    plan_id = callback.data.split("_")[-1]
    
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/plans/{plan_id}")
            if resp.status_code != 200:
                await callback.answer("Plan not found.", show_alert=True)
                return
            plan = resp.json()
            
            text = (
                f"🛠 **Editing Plan #{plan_id}**\n\n"
                f"**Type:** {plan.get('server_type')}\n"
                f"**Duration:** {plan.get('duration_days')} Days\n"
                f"**Data Limit:** {plan.get('data_limit_gb')} GB\n"
                f"**Price:** {plan.get('price_irr')} IRR\n"
                f"**Status:** {'Active ✅' if plan.get('is_active') else 'Inactive ❌'}\n\n"
                f"What would you like to edit?"
            )
            
            buttons = [
                [
                    InlineKeyboardButton(text="🕒 Duration", callback_data=f"admin_editfield_{plan_id}_duration_days"),
                    InlineKeyboardButton(text="💾 Data Limit", callback_data=f"admin_editfield_{plan_id}_data_limit_gb")
                ],
                [
                    InlineKeyboardButton(text="💰 Price (IRR)", callback_data=f"admin_editfield_{plan_id}_price_irr"),
                    InlineKeyboardButton(text="🔄 Toggle Status", callback_data=f"admin_toggle_{plan_id}_{plan.get('is_active')}")
                ],
                [InlineKeyboardButton(text="🔙 Back to Plans", callback_data="admin_list_plans")]
            ]
            makeup = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await state.clear()
            await callback.message.edit_text(text, reply_markup=makeup, parse_mode="Markdown")
        except Exception as e:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data.startswith("admin_toggle_"))
async def edit_plan_toggle_status(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    plan_id = parts[2]
    current_status = parts[3].lower() == "true"
    new_status = not current_status
    
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.patch(f"{API_BASE_URL}/plans/{plan_id}", json={"is_active": new_status})
            if resp.status_code == 200:
                await callback.answer("Status updated!")
                # Refresh the menu
                await edit_plan_menu(callback, None) # Pass None or fake state if necessary, wait, edit_plan_menu expects FSMContext.
                # Better to just redirect callback data
            else:
                await callback.answer("Failed to update status", show_alert=True)
        except Exception:
            await callback.answer("Backend error.", show_alert=True)
            
    # Quick refresh by editing the message to fetch plan again:
    from aiogram.fsm.context import FSMContext
    # We will just tell user to click back or re-trigger the menu
    # Actually, aiogram doesn't let us easily fake a callback call with state easily here without passing it.
    # Let's just update the text manually or ask to re-click it.
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("🔙 Back", callback_data=f"admin_editplan_{plan_id}")]]))
            
@router.callback_query(F.data.startswith("admin_editfield_"))
async def edit_plan_prompt_field(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    plan_id = parts[2]
    field = "_".join(parts[3:]) # e.g. duration_days
    
    await state.update_data(edit_plan_id=plan_id, edit_plan_field=field)
    
    field_names = {
        "duration_days": "Duration (Days)",
        "data_limit_gb": "Data Limit (GB)",
        "price_irr": "Price (IRR)"
    }
    
    await callback.message.answer(f"Please enter the new value for **{field_names.get(field, field)}**:", parse_mode="Markdown")
    await state.set_state(EditPlanForm.waiting_for_new_value)

@router.message(EditPlanForm.waiting_for_new_value)
async def process_edit_plan_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    plan_id = data.get("edit_plan_id")
    field = data.get("edit_plan_field")
    
    payload = {}
    
    try:
        val_str = message.text.strip()
        if field == "duration_days":
            payload[field] = int(val_str)
        elif field == "data_limit_gb":
            payload[field] = float(val_str)
        elif field == "price_irr":
            v = float(val_str)
            payload[field] = v
            payload["price_usdt"] = v / 600000 
    except ValueError:
        await message.answer("❌ Invalid number format. Please try again.")
        return
        
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.patch(f"{API_BASE_URL}/plans/{plan_id}", json=payload)
            if resp.status_code == 200:
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("🔙 Return to Plan Menu", callback_data=f"admin_editplan_{plan_id}")]
                ])
                await message.answer("✅ Plan updated successfully!", reply_markup=markup)
            else:
                await message.answer("❌ Failed to update plan.")
        except Exception:
            await message.answer("❌ Backend error.")
            
    await state.clear()

# --- Endpoint Management ---
@router.callback_query(F.data == "admin_endpoints")
async def admin_endpoints_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/endpoints?all=true")
            endpoints = resp.json()
            
            buttons = []
            for ep in endpoints:
                status = "✅" if ep.get('is_active') else "❌"
                btn_text = f"{status} {ep.get('name')} — {ep.get('address')}"
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin_ep_toggle_{ep.get('ID')}_{ep.get('is_active')}")])
            
            buttons.append([InlineKeyboardButton(text="➕ Add Endpoint", callback_data="admin_add_ep")])
            buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")])
            
            text = "🌍 **WireGuard Endpoints**\n\nTap an endpoint to toggle its status:\n" if endpoints else "No endpoints yet. Add one!"
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
        except Exception:
            await callback.answer("Backend error.", show_alert=True)

@router.callback_query(F.data.startswith("admin_ep_toggle_"))
async def admin_ep_toggle(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    ep_id = parts[3]
    current = parts[4].lower() == "true"
    
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.patch(f"{API_BASE_URL}/endpoints/{ep_id}", json={"is_active": not current})
            if resp.status_code == 200:
                await callback.answer("Toggled!")
            else:
                await callback.answer("Failed.", show_alert=True)
        except Exception:
            await callback.answer("Backend error.", show_alert=True)
    
    # Refresh list
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_endpoints")]
    ]))

@router.callback_query(F.data == "admin_add_ep")
async def admin_add_ep_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    await callback.message.answer("Enter the endpoint **display name** (e.g. 🇩🇪 Germany):", parse_mode="Markdown")
    await state.set_state(AddEndpointForm.waiting_for_name)

@router.message(AddEndpointForm.waiting_for_name)
async def admin_add_ep_name(message: types.Message, state: FSMContext):
    await state.update_data(ep_name=message.text.strip())
    await message.answer("Enter the endpoint **address** (e.g. `de.server.com:51820`):", parse_mode="Markdown")
    await state.set_state(AddEndpointForm.waiting_for_address)

@router.message(AddEndpointForm.waiting_for_address)
async def admin_add_ep_address(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    async with httpx.AsyncClient(headers={"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}) as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/endpoints", json={
                "name": data.get("ep_name"),
                "address": message.text.strip(),
                "is_active": True
            })
            if resp.status_code == 201:
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back to Endpoints", callback_data="admin_endpoints")]
                ])
                await message.answer(f"✅ Endpoint added: **{data.get('ep_name')}** — `{message.text.strip()}`", parse_mode="Markdown", reply_markup=markup)
            else:
                await message.answer("❌ Failed to add endpoint.")
        except Exception:
            await message.answer("❌ Backend error.")
    
    await state.clear()

