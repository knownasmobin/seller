from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import httpx
import os

router = Router()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1")
ADMIN_CARD_NUMBER = os.getenv("ADMIN_CARD_NUMBER", "1234-5678-9012-3456")

class PaymentState(StatesGroup):
    waiting_for_screenshot = State()

@router.callback_query(F.data.startswith("pay_card_"))
async def process_card_payment(callback: CallbackQuery, state: FSMContext):
    plan_id = callback.data.split("_")[-1]
    lang = "fa" if "fa" in (callback.fromuser.language_code or "") else "en"

    # Save plan ID in context
    await state.update_data(plan_id=plan_id)

    text = (
        f"💳 Please transfer the amount to this card number:\n"
        f" `{ADMIN_CARD_NUMBER}`\n\n"
        f"After transferring, please send the screenshot of your receipt here."
    ) if lang == "en" else (
        f"💳 لطفا مبلغ را به این شماره کارت واریز کنید:\n"
        f" `{ADMIN_CARD_NUMBER}`\n\n"
        f"سپس اسکرین شات رسید پرداخت خود را همینجا ارسال کنید."
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(PaymentState.waiting_for_screenshot)

ADMIN_ID = os.getenv("ADMIN_ID", "123456789")  # Ideally set this in .env

@router.message(PaymentState.waiting_for_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    plan_id = data.get("plan_id")
    lang = "fa" if "fa" in (message.from_user.language_code or "") else "en"

    file_id = message.photo[-1].file_id

    async with httpx.AsyncClient() as client:
        try:
            order_resp = await client.post(f"{API_BASE_URL}/orders/", json={
                "telegram_id": message.from_user.id,
                "plan_id": int(plan_id),
                "payment_method": "card",
                "amount": 100000.0  # In reality we fetch price from plan
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
            
            try:
                await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=admin_text, reply_markup=admin_markup, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Could not submit to admin: {e}")

            text = "✅ Receipt received! We will verify it shortly and send your config." if lang == "en" else "✅ رسید دریافت شد! پس از تایید مدیریت کانفیگ شما ارسال خواهد شد."
            await message.answer(text)
            await state.clear()
        except Exception as e:
            text = "❌ Error processing your request." if lang == "en" else "❌ خطا در پردازش درخواست شما."
            await message.answer(text)
            await state.clear()

@router.callback_query(F.data.startswith("approve_order_"))
async def process_approve_order(callback: CallbackQuery, bot):
    order_id = callback.data.split("_")[-1]
    
    # Ideally, we call an API endpoint to mark the order as approved and generate the config
    # For now, we mock success
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **APPROVED**")
    await callback.answer("Order approved!")
    
    # We would fetch user ID from order here via API, but we don't have it easily without DB.
    # We'll just assume admin knows.
    
@router.callback_query(F.data.startswith("reject_order_"))
async def process_reject_order(callback: CallbackQuery, bot):
    order_id = callback.data.split("_")[-1]
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **REJECTED**")
    await callback.answer("Order rejected!")

@router.callback_query(F.data.startswith("pay_crypto_"))
async def process_crypto_payment(callback: CallbackQuery):
    plan_id = callback.data.split("_")[-1]
    lang = "fa" if "fa" in (callback.from_user.language_code or "") else "en"

    # In a real app, we would make a POST to our Go backend to create the Order and get the Oxapay Link
    # Since we didn't expose an Oxapay specific endpoint in Go yet, we will mock the URL generation here
    # or pretend the backend does it.
    
    text = (
        "🔗 Generating your Crypto payment link..."
    ) if lang == "en" else (
        "🔗 در حال ایجاد لینک پرداخت کریپتو..."
    )
    
    msg = await callback.message.edit_text(text)
    
    async with httpx.AsyncClient() as client:
        try:
            # We create an order first
            order_resp = await client.post(f"{API_BASE_URL}/orders/", json={
                "telegram_id": callback.from_user.id,
                "plan_id": int(plan_id),
                "payment_method": "crypto",
                "amount": 2.5  # USDT mock price
            })
            order_data = order_resp.json()
            order_id = order_data.get("ID")
            
            # Now we use the actual payLink from the backend
            payment_url = order_data.get("payLink")
            if not payment_url:
                payment_url = f"https://oxapay.com/pay/{order_id}test" # Fallback test link
            
            success_text = (
                f"💳 **Order #{order_id} created!**\n\n"
                f"Please click the button below to pay via USDT (TRC20/BEP20).\n"
                f"Your config will be generated automatically once the blockchain confirms the transaction."
            ) if lang == "en" else (
                f"💳 **سفارش #{order_id} ایجاد شد!**\n\n"
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
