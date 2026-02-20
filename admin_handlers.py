import logging
import os
import httpx
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")
ADMIN_ID = os.getenv("ADMIN_ID")

class AddPlanForm(StatesGroup):
    waiting_for_protocol = State()
    waiting_for_duration = State()
    waiting_for_data_limit = State()
    waiting_for_price = State()

def is_admin(telegram_id: int) -> bool:
    return bool(ADMIN_ID and str(telegram_id) == ADMIN_ID)

# --- Admin Panel Entry ---
@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("You are not authorized.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add New Plan", callback_data="admin_add_plan")],
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
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE_URL}/plans", json=plan_payload)
            if resp.status_code == 201:
                await message.answer(f"✅ Plan added successfully!\n\nType: {data['server_type']}\nDays: {data['duration_days']}\nGB: {data['data_limit_gb']}\nPrice: {price_irr} IRR")
            else:
                logging.error(f"Failed to add plan: {resp.text}")
                await message.answer("❌ Failed to add plan due to server error.")
                
        await state.clear()
        
    except ValueError:
        await message.answer("Please enter a valid numeric price.")
