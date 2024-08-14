from aiogram import types, Router
from aiogram.filters import Command
from utils.custom_filter import IsBan, IsPrivate, IsAdmin
from utils.kb import main_admin
from utils.database.database import database as db_manager
from message import Message


router = Router()

@router.message(Command("admin"), IsPrivate(), IsAdmin(), IsBan())
async def admin_panel(message: types.Message):
    await message.answer(Message.ADMIN.format(message.chat.id), reply_markup=main_admin.as_markup())