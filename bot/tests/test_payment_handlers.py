import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import CallbackQuery, User, Message
from aiogram.fsm.context import FSMContext
from payment_handlers import process_card_payment, PaymentState

@pytest.mark.asyncio
async def test_process_card_payment():
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.from_user = User(id=123456, is_bot=False, first_name="User", language_code="en")
    mock_callback.data = "pay_card_1_0"
    
    mock_message = AsyncMock(spec=Message)
    mock_message.edit_text = AsyncMock()
    mock_callback.message = mock_message
    
    mock_state = AsyncMock(spec=FSMContext)

    with patch("payment_handlers.get_user_lang", new_callable=AsyncMock) as mock_lang:
        mock_lang.return_value = "en"
        with patch("payment_handlers.get_card_number", new_callable=AsyncMock) as mock_card:
            mock_card.return_value = "1111-2222-3333-4444"
            
            await process_card_payment(mock_callback, mock_state)
            
            mock_state.update_data.assert_awaited_once_with(plan_id="1", endpoint_id=0)
            mock_state.set_state.assert_awaited_once_with(PaymentState.waiting_for_screenshot)
            
            mock_callback.message.edit_text.assert_awaited_once()
            args = mock_callback.message.edit_text.call_args[0][0]
            assert "1111-2222-3333-4444" in args
