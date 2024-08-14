from aiogram import types, Router
from message import Message
from utils.custom_filter import IsBan, IsPrivate
from utils.database.database import database as db_manager
from utils.database.models import Distributor
from utils.kb import main_user, main_dist, generate_promo
from aiogram.filters import Command


router = Router()

@router.message(Command("dist"), IsBan(), IsPrivate())
async def process_user(message: types.Message):
    async for session in db_manager.get_session():
        if await Distributor.find_distributor_by_telegram_id(session, message.from_user.id):
            await message.answer(Message.ACTION_DIST, reply_markup=main_dist.as_markup())
        else:
            await message.answer(Message.GENERATE_PROMO, reply_markup=generate_promo.as_markup())
        await session.commit()

@router.message(Command("user"), IsBan(), IsPrivate())
async def process_user(message: types.Message):
    await message.answer(Message.ACTION_DIST, reply_markup=main_user.as_markup())
    