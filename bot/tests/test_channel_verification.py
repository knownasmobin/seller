import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, User, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot import (
    ChannelVerificationMiddleware,
    get_required_channel,
    check_channel_membership,
    channel_verified_cache,
    auth_cache,
    get_required_channel_link,
)
import httpx

@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    return bot

@pytest.fixture
def mock_message():
    message = AsyncMock(spec=Message)
    message.from_user = User(id=123456, is_bot=False, first_name="Test", language_code="en")
    message.answer = AsyncMock()
    return message

@pytest.fixture
def mock_callback():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = User(id=123456, is_bot=False, first_name="Test", language_code="en")
    callback.message = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    callback.bot = AsyncMock()
    return callback

@pytest.fixture
def admin_user():
    return User(id=999999, is_bot=False, first_name="Admin", language_code="en")

@pytest.mark.asyncio
async def test_get_required_channel_empty(mock_message, mock_bot):
    """Test getting required channel when not set"""
    with patch("bot.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"required_channel": ""}

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client.return_value.__aexit__.return_value = None

        channel = await get_required_channel()
        assert channel == ""

@pytest.mark.asyncio
async def test_get_required_channel_set(mock_message, mock_bot):
    """Test getting required channel when set"""
    with patch("bot.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"required_channel": "@mychannel"}

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client.return_value.__aexit__.return_value = None

        channel = await get_required_channel()
        assert channel == "@mychannel"

@pytest.mark.asyncio
async def test_check_channel_membership_no_channel(mock_bot):
    """Test channel membership check when no channel is required"""
    is_member = await check_channel_membership(mock_bot, 123456, "")
    assert is_member is True

@pytest.mark.asyncio
async def test_check_channel_membership_user_is_member(mock_bot):
    """Test channel membership check when user is a member"""
    from aiogram.types import ChatMember
    
    mock_member = MagicMock()
    mock_member.status = "member"
    mock_bot.get_chat_member = AsyncMock(return_value=mock_member)
    
    is_member = await check_channel_membership(mock_bot, 123456, "@mychannel")
    assert is_member is True
    mock_bot.get_chat_member.assert_awaited_once_with(chat_id="@mychannel", user_id=123456)

@pytest.mark.asyncio
async def test_check_channel_membership_user_not_member(mock_bot):
    """Test channel membership check when user is not a member"""
    mock_member = MagicMock()
    mock_member.status = "left"
    mock_bot.get_chat_member = AsyncMock(return_value=mock_member)
    
    is_member = await check_channel_membership(mock_bot, 123456, "@mychannel")
    assert is_member is False

@pytest.mark.asyncio
async def test_channel_middleware_no_channel_required(mock_message, mock_bot):
    """Test middleware allows access when no channel is required"""
    middleware = ChannelVerificationMiddleware()
    handler = AsyncMock()
    
    # Clear cache
    channel_verified_cache.clear()
    auth_cache.clear()
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link:
        mock_get_channel.return_value = ""
        mock_get_link.return_value = ""
        
        data = {"bot": mock_bot}
        await middleware(handler, mock_message, data)
        
        handler.assert_awaited_once()

@pytest.mark.asyncio
async def test_channel_middleware_user_is_member(mock_message, mock_bot):
    """Test middleware allows access when user is a member"""
    middleware = ChannelVerificationMiddleware()
    handler = AsyncMock()
    
    # Clear cache
    channel_verified_cache.clear()
    auth_cache.clear()
    auth_cache.add(123456)
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_check.return_value = True
        
        data = {"bot": mock_bot}
        await middleware(handler, mock_message, data)
        
        handler.assert_awaited_once()
        assert 123456 in channel_verified_cache

@pytest.mark.asyncio
async def test_channel_middleware_user_not_member_shows_message(mock_message, mock_bot):
    """Test middleware shows join message when user is not a member"""
    middleware = ChannelVerificationMiddleware()
    handler = AsyncMock()
    
    # Clear cache
    channel_verified_cache.clear()
    auth_cache.clear()
    auth_cache.add(123456)
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_check.return_value = False
        
        data = {"bot": mock_bot}
        await middleware(handler, mock_message, data)
        
        # Handler should not be called
        handler.assert_not_awaited()
        # Message should be sent
        mock_message.answer.assert_awaited_once()
        args, kwargs = mock_message.answer.call_args
        assert "Channel Membership Required" in args[0]
        assert "reply_markup" in kwargs

@pytest.mark.asyncio
async def test_channel_middleware_skips_admin(mock_message, mock_bot, admin_user):
    """Test middleware skips verification for admins"""
    middleware = ChannelVerificationMiddleware()
    handler = AsyncMock()
    
    admin_message = AsyncMock(spec=Message)
    admin_message.from_user = admin_user
    admin_message.answer = AsyncMock()
    
    # Clear cache
    channel_verified_cache.clear()
    auth_cache.clear()
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("os.getenv") as mock_getenv:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_getenv.return_value = "999999"  # Admin ID
        
        data = {"bot": mock_bot}
        await middleware(handler, admin_message, data)
        
        # Handler should be called without checking membership
        handler.assert_awaited_once()
        admin_message.answer.assert_not_awaited()

@pytest.mark.asyncio
async def test_channel_middleware_uses_cache(mock_message, mock_bot):
    """Test middleware uses cache for verified users"""
    middleware = ChannelVerificationMiddleware()
    handler = AsyncMock()
    
    # Add user to cache
    channel_verified_cache.add(123456)
    auth_cache.add(123456)
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        
        data = {"bot": mock_bot}
        await middleware(handler, mock_message, data)
        
        # Handler should be called
        handler.assert_awaited_once()
        # Membership check should not be called (using cache)
        mock_check.assert_not_awaited()
    
    # Cleanup
    channel_verified_cache.discard(123456)

@pytest.mark.asyncio
async def test_verify_channel_callback_success(mock_callback):
    """Test verify channel callback when user joins"""
    from handlers import verify_channel_callback
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check, \
         patch("handlers.get_user_lang", new_callable=AsyncMock) as mock_lang:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_check.return_value = True
        mock_lang.return_value = "en"
        
        await verify_channel_callback(mock_callback)
        
        mock_callback.answer.assert_awaited_once()
        # Should add to cache
        assert 123456 in channel_verified_cache
    
    # Cleanup
    channel_verified_cache.discard(123456)

@pytest.mark.asyncio
async def test_verify_channel_callback_not_member(mock_callback):
    """Test verify channel callback when user hasn't joined"""
    from handlers import verify_channel_callback
    
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check, \
         patch("handlers.get_user_lang", new_callable=AsyncMock) as mock_lang:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_check.return_value = False
        mock_lang.return_value = "en"
        
        await verify_channel_callback(mock_callback)
        
        mock_callback.answer.assert_awaited_once()
        # Should show error message
        args, kwargs = mock_callback.answer.call_args
        assert "haven't joined" in args[0] or "joined" in args[0]


@pytest.mark.asyncio
async def test_channel_gate_e2e_flow_block_verify_then_allow(mock_message, mock_callback, mock_bot):
    """End-to-end style flow: blocked first, then verify callback succeeds, then middleware allows."""
    from handlers import verify_channel_callback

    middleware = ChannelVerificationMiddleware()
    handler = AsyncMock()

    channel_verified_cache.clear()
    auth_cache.clear()
    auth_cache.add(123456)

    # Step 1: User is not a member -> blocked by middleware
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_check.return_value = False

        await middleware(handler, mock_message, {"bot": mock_bot})

        handler.assert_not_awaited()
        mock_message.answer.assert_awaited_once()
        assert 123456 not in channel_verified_cache

    # Step 2: User presses verify and is now a member -> cache updated
    mock_callback.from_user = mock_message.from_user
    mock_callback.bot = mock_bot
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check, \
         patch("handlers.get_user_lang", new_callable=AsyncMock) as mock_lang:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""
        mock_check.return_value = True
        mock_lang.return_value = "en"

        await verify_channel_callback(mock_callback)

        assert 123456 in channel_verified_cache

    # Step 3: Middleware now allows the user without re-checking membership
    handler.reset_mock()
    mock_message.answer.reset_mock()
    with patch("bot.get_required_channel", new_callable=AsyncMock) as mock_get_channel, \
         patch("bot.get_required_channel_link", new_callable=AsyncMock) as mock_get_link, \
         patch("bot.check_channel_membership", new_callable=AsyncMock) as mock_check:
        mock_get_channel.return_value = "@mychannel"
        mock_get_link.return_value = ""

        await middleware(handler, mock_message, {"bot": mock_bot})

        handler.assert_awaited_once()
        mock_check.assert_not_awaited()
        mock_message.answer.assert_not_awaited()

    channel_verified_cache.clear()

