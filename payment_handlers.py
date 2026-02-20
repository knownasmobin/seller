from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import httpx
import os
import logging
from utils import get_user_lang

router = Router()
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3000/api/v1")

async def get_card_number():
    """Fetch card number from backend (dashboard-editable), fallback to env var."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE_URL}/admin/settings", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                card = data.get("admin_card_number", "")
                if card:
                    return card
    except Exception:
        pass
    return os.getenv("ADMIN_CARD_NUMBER", "1234-5678-9012-3456")

class PaymentState(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_manual_config = State()

@router.callback_query(F.data.startswith("pay_card_"))
async def process_card_payment(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    plan_id = parts[2]
    endpoint_id = int(parts[3]) if len(parts) > 3 else 0
    lang = await get_user_lang(callback.from_user.id)

    # Save plan ID and endpoint ID in context
    await state.update_data(plan_id=plan_id, endpoint_id=endpoint_id)

    card_number = await get_card_number()

    text = (
        f"💳 Please transfer the amount to this card number:\n"
        f" `{card_number}`\n\n"
        f"After transferring, please send the screenshot of your receipt here."
    ) if lang == "en" else (
        f"💳 لطفا مبلغ را به این شماره کارت واریز کنید:\n"
        f" `{card_number}`\n\n"
        f"سپس اسکرین شات رسید پرداخت خود را همینجا ارسال کنید."
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(PaymentState.waiting_for_screenshot)

ADMIN_IDS = [x.strip() for x in os.getenv("ADMIN_ID", "123456789").split(",") if x.strip()]

@router.message(PaymentState.waiting_for_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    plan_id = data.get("plan_id")
    endpoint_id = data.get("endpoint_id", 0)
    lang = await get_user_lang(message.from_user.id)

    file_id = message.photo[-1].file_id

    async with httpx.AsyncClient() as client:
        try:
            # Fetch the actual plan to get the real price
            plan_resp = await client.get(f"{API_BASE_URL}/plans/{plan_id}")
            if plan_resp.status_code != 200:
                raise Exception("Plan not found")
            plan_data = plan_resp.json()
            real_price_irr = plan_data.get("price_irr", 0.0)

            # Create the order
            order_resp = await client.post(f"{API_BASE_URL}/orders/", json={
                "telegram_id": message.from_user.id,
                "plan_id": int(plan_id),
                "endpoint_id": int(endpoint_id),
                "payment_method": "card",
                "amount": float(real_price_irr)
            })
            order_data = order_resp.json()
            order_id = order_data.get("ID")
            
            # Send screenshot to Admin group for approval using order_id and file_id
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            admin_markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_order_{order_id}"),
                    InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_order_{order_id}")
                ]
            ])
            admin_text = f"💳 **New Card Payment**\n\n**Order ID:** {order_id}\n**User ID:** {message.from_user.id}\n**Plan ID:** {plan_id}"
            
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_photo(chat_id=admin_id, photo=file_id, caption=admin_text, reply_markup=admin_markup, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Could not submit to admin {admin_id}: {e}")

            text = "✅ Receipt received! We will verify it shortly and send your config." if lang == "en" else "✅ رسید دریافت شد! پس از تایید مدیریت کانفیگ شما ارسال خواهد شد."
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Main Menu" if lang == "en" else "🔙 منوی اصلی", callback_data="main_menu")]
            ])
            await message.answer(text, reply_markup=markup)
            await state.clear()
        except Exception as e:
            text = "❌ Error processing your request." if lang == "en" else "❌ خطا در پردازش درخواست شما."
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Main Menu" if lang == "en" else "🔙 منوی اصلی", callback_data="main_menu")]
            ])
            await message.answer(text, reply_markup=markup)
            await state.clear()

@router.callback_query(F.data.startswith("approve_order_"))
async def process_approve_order(callback: CallbackQuery, bot):
    order_id = callback.data.split("_")[-1]
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/orders/{order_id}/approve", timeout=65.0)
            data = resp.json()
            
            if resp.status_code == 200:
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n✅ **APPROVED** — VPN config provisioned and sent to user."
                )
                await callback.answer("✅ Order approved! Config sent to user.", show_alert=True)
            else:
                error_type = data.get("error", "")
                error_msg = data.get("message", "Unknown error")
                
                if error_type == "provisioning_failed":
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⚙️ Set Manual Config", callback_data=f"manual_config_{order_id}")],
                        [InlineKeyboardButton(text="❌ Reject Order instead", callback_data=f"reject_order_{order_id}")]
                    ])
                    # Update caption to show it failed to provision
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\n⚠️ **Provisioning Failed!** Server or API is down.",
                        reply_markup=markup
                    )
                    await callback.answer(f"⚠️ Failed to provision config.", show_alert=True)
                else:
                    await callback.message.edit_caption(
                        caption=callback.message.caption + f"\n\n⚠️ Approve issue: {error_msg}"
                    )
                    await callback.answer(f"Issue: {error_msg}", show_alert=True)
        except Exception as e:
            logging.error(f"Approve order error: {e}")
            await callback.answer("❌ Backend connection timeout/error", show_alert=True)
    
@router.callback_query(F.data.startswith("reject_order_"))
async def process_reject_order(callback: CallbackQuery, bot):
    order_id = callback.data.split("_")[-1]
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/orders/{order_id}/reject")
            if resp.status_code == 200:
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n❌ **REJECTED** — User has been notified."
                )
                await callback.answer("Order rejected.", show_alert=True)
            else:
                await callback.answer("Error rejecting order", show_alert=True)
        except Exception as e:
            logging.error(f"Reject order error: {e}")
            await callback.answer("❌ Backend connection error", show_alert=True)

@router.callback_query(F.data.startswith("pay_crypto_"))
async def process_crypto_payment(callback: CallbackQuery):
    parts = callback.data.split("_")
    plan_id = parts[2]
    endpoint_id = int(parts[3]) if len(parts) > 3 else 0
    lang = await get_user_lang(callback.from_user.id)

    text = (
        "🔗 Generating your Crypto payment link..."
    ) if lang == "en" else (
        "🔗 در حال ایجاد لینک پرداخت کریپتو..."
    )
    
    if getattr(callback.message, "photo", None):
        try:
            await callback.message.delete()
        except Exception:
            pass
        msg = await callback.message.answer(text)
    else:
        msg = await callback.message.edit_text(text)
    
    async with httpx.AsyncClient() as client:
        try:
            # Fetch the actual plan to get the real crypto price
            plan_resp = await client.get(f"{API_BASE_URL}/plans/{plan_id}")
            if plan_resp.status_code != 200:
                raise Exception("Plan not found")
            plan_data = plan_resp.json()
            real_price_usdt = plan_data.get("price_usdt", 0.0)

            # We create an order first
            order_resp = await client.post(f"{API_BASE_URL}/orders/", json={
                "telegram_id": callback.from_user.id,
                "plan_id": int(plan_id),
                "endpoint_id": int(endpoint_id),
                "payment_method": "crypto",
                "amount": float(real_price_usdt)
            })
            order_data = order_resp.json()
            order_id = order_data.get("ID")
            
            # Now we use the actual payLink from the backend
            payment_url = order_data.get("payLink")
            if not payment_url:
                payment_url = f"https://oxapay.com/pay/{order_id}test" # Fallback test link
            
            success_text = (
                f"💳 **Order #{order_id} created!**\n\n"
                f"**Amount:** {real_price_usdt} USDT\n"
                f"Please click the button below to pay via USDT (TRC20/BEP20).\n"
                f"Your config will be generated automatically once the blockchain confirms the transaction."
            ) if lang == "en" else (
                f"💳 **سفارش #{order_id} ایجاد شد!**\n\n"
                f"**مبلغ:** {real_price_usdt} تتر (USDT)\n"
                f"لطفا برای پرداخت با USDT روی دکمه زیر کلیک کنید.\n"
                f"کانفیگ شما بلافاصله پس از تایید شبکه کریپتو به صورت خودکار صادر خواهد شد."
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Pay Now (Oxapay)", url=payment_url)],
                [InlineKeyboardButton(text="🔙 Back", callback_data="buy_menu")]
            ])
            
            await msg.edit_text(success_text, parse_mode="Markdown", reply_markup=markup)
            
        except Exception as e:
            error_text = "❌ Error connecting to payment gateway." if lang == "en" else "❌ خطا در ارتباط با درگاه پرداخت."
            await msg.edit_text(error_text)
@router.callback_query(F.data.startswith("manual_config_"))
async def process_manual_config_btn(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[-1]
    await state.update_data(manual_order_id=order_id)
    await state.set_state(PaymentState.waiting_for_manual_config)
    
    await callback.message.reply(
        f"⚙️ **Manual Provisioning for Order #{order_id}**\n\n"
        "Please type or paste the full connection link (e.g. `vless://...`) below:",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(PaymentState.waiting_for_manual_config)
async def process_manual_config_input(message: Message, state: FSMContext):
    config_link = message.text.strip()
    data = await state.get_data()
    order_id = data.get("manual_order_id")

    if not order_id:
        await message.answer("❌ Error: Lost order context. Please click the 'Set Manual Config' button again.")
        await state.clear()
        return

    wait_msg = await message.answer("🔄 Sending manual config to backend...")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{API_BASE_URL}/orders/{order_id}/manual_provision",
                json={"config_link": config_link},
                timeout=60.0
            )
            resp_data = resp.json()

            if resp.status_code == 200:
                await wait_msg.edit_text("✅ Config manually saved! The user has been notified.")
            else:
                error_msg = resp_data.get("error", "Unknown error")
                await wait_msg.edit_text(f"❌ Failed to save config: {error_msg}")
        except Exception as e:
            logging.error(f"Manual provision error: {e}")
            await wait_msg.edit_text("❌ Backend connection timeout/error.")

    await state.clear()
