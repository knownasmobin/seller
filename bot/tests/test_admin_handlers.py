import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import CallbackQuery, User, Message
from aiogram.fsm.context import FSMContext
from admin_handlers import show_admin_panel, add_plan_start

@pytest.fixture
def mock_admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_ID", "999999")

@pytest.mark.asyncio
@patch("admin_handlers.is_admin", return_value=False)
async def test_show_admin_panel_unauthorized(mock_is_admin):
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.from_user = User(id=111111, is_bot=False, first_name="User")
    mock_callback.answer = AsyncMock()

    await show_admin_panel(mock_callback)

    mock_callback.answer.assert_awaited_once()
    assert "not authorized" in mock_callback.answer.call_args[0][0]

@pytest.mark.asyncio
@patch("admin_handlers.is_admin", return_value=True)
async def test_show_admin_panel_authorized(mock_is_admin):
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.from_user = User(id=999999, is_bot=False, first_name="Admin")
    mock_callback.answer = AsyncMock()
    
    mock_message = AsyncMock(spec=Message)
    mock_message.edit_text = AsyncMock()
    mock_callback.message = mock_message

    await show_admin_panel(mock_callback)

    mock_callback.message.edit_text.assert_awaited_once()
    assert "Admin Panel" in mock_callback.message.edit_text.call_args[0][0]

@pytest.mark.asyncio
@patch("admin_handlers.is_admin", return_value=True)
async def test_add_plan_start_authorized(mock_is_admin):
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.from_user = User(id=999999, is_bot=False, first_name="Admin")
    mock_callback.answer = AsyncMock()
    
    mock_message = AsyncMock(spec=Message)
    mock_message.edit_text = AsyncMock()
    mock_callback.message = mock_message
    
    mock_state = AsyncMock(spec=FSMContext)

    await add_plan_start(mock_callback, mock_state)

    mock_callback.message.edit_text.assert_awaited_once()
    mock_state.set_state.assert_awaited_once()
