from aiogram.filters import Filter
from aiogram import types
from loguru import logger

from message import Message
from utils.database.models import User
from utils.database.database import database as db_manager
from utils.support_method import can_convert_to_float


class IsPrivate(Filter):
    async def __call__(self, message: types.Message | types.CallbackQuery) -> bool:
        if type(message) is types.CallbackQuery:
            return message.message.chat.type == "private"
        else:
            return message.chat.type == "private"

class IsGroup(Filter):
    async def __call__(self, message: types.Message | types.CallbackQuery) -> bool:
        if type(message) is types.CallbackQuery:
            return message.message.chat.type in ["group", "supergroup"]
        else:
            return message.chat.type in ["group", "supergroup"]

class IsAdmin(Filter):
    async def __call__(self, message: types.Message) -> bool:
        async for session in db_manager.get_session():
            admins = await User.get_admin_telegram_ids(session=session)
            await session.commit()
        if not admins:
            logger.error(Message.NO_ADMINS_FOUND)
            return False
        return message.from_user.id in list(map(int, admins))

class IsSuperAdmin(Filter):
    async def __call__(self, message: types.Message | types.CallbackQuery) -> bool:
        return message.from_user.id == 6044110141

class IsFloat(Filter):
    async def __call__(self, message: types.Message) -> bool:
        if can_convert_to_float(message.text):
            return True
        await message.answer(Message.ERROR_MONEY)
        return False

class IsBan(Filter):
    async def __call__(self, message: types.Message) -> bool:
        async for session in db_manager.get_session():
            is_ban = await User.is_user_banned(session, message.from_user.id)
            await session.commit()
        if is_ban:
            await message.answer(Message.BAN_USER)
        return not is_ban

class IsUserAddOrder(Filter):
    async def __call__(self, callback: types.CallbackQuery) -> bool:
        async for session in db_manager.get_session():
            result = await User.has_completed_or_canceled_orders(session, callback.from_user.id)
            await session.commit()
        logger.info(result)
        if not result:
            await callback.message.answer(Message.NO_ORDER)
        return result