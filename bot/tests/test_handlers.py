import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, User
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandObject
from bot import cmd_start, RegistrationState

@pytest.mark.asyncio
async def test_cmd_start_new_user_success():
    # 1. Setup mock message and state
    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = User(id=123456, is_bot=False, first_name="Test", language_code="en")
    mock_message.answer = AsyncMock()
    
    mock_command = CommandObject(prefix="/", command="start", args="")
    
    mock_state = AsyncMock(spec=FSMContext)
    
    # 2. Patch the get_or_create_user function to simulate successful backend response
    with patch("bot.get_or_create_user", new_callable=AsyncMock) as mock_api:
        # returns (user_data, error_data)
        mock_api.return_value = ({"language": "en"}, None)
        
        # 3. Call the handler
        await cmd_start(mock_message, mock_command, mock_state)
        
        # 4. Verify the state was cleared
        mock_state.clear.assert_awaited_once()
        
        # 5. Verify a message was sent with the welcome text
        mock_message.answer.assert_awaited_once()
        args, kwargs = mock_message.answer.call_args
        assert "Welcome to our VPN Store!" in args[0]
        assert "reply_markup" in kwargs

@pytest.mark.asyncio
async def test_cmd_start_requires_invite_code():
    # 1. Setup mock message and state
    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = User(id=123456, is_bot=False, first_name="Test", language_code="fa")
    mock_message.answer = AsyncMock()
    
    mock_command = CommandObject(prefix="/", command="start", args="")
    
    mock_state = AsyncMock(spec=FSMContext)
    
    # 2. Patch the get_or_create_user function to simulate invite requirement error
    with patch("bot.get_or_create_user", new_callable=AsyncMock) as mock_api:
        # returns (user_data, error_data)
        mock_api.return_value = (None, {"error": "invite_code_required"})
        
        # 3. Call the handler
        await cmd_start(mock_message, mock_command, mock_state)
        
        # 4. Verify FSM state was set to waiting_for_invite_code
        mock_state.set_state.assert_awaited_once_with(RegistrationState.waiting_for_invite_code)
        
        # 5. Verify the invite code prompt was sent
        mock_message.answer.assert_awaited_once()
        args, kwargs = mock_message.answer.call_args
        assert "لطفاً کد دعوت خود را وارد کنید" in args[0]

@pytest.mark.asyncio
async def test_process_invite_code_success():
    from bot import process_invite_code
    
    # 1. Setup mock message
    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = User(id=123456, is_bot=False, first_name="Test", language_code="en")
    mock_message.text = "VALID_CODE"
    mock_message.answer = AsyncMock()
    
    mock_state = AsyncMock(spec=FSMContext)
    
    # 2. Patch API
    with patch("bot.get_or_create_user", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = ({"language": "en"}, None)
        
        # 3. Call handler
        await process_invite_code(mock_message, mock_state)
        
        # 4. Verify success
        mock_state.clear.assert_awaited_once()
        mock_message.answer.assert_awaited_once()
        assert "Registration Successful!" in mock_message.answer.call_args[0][0]
