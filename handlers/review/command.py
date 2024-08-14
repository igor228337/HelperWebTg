from aiogram import types, Router
from message import Message
from utils.custom_filter import IsBan, IsPrivate
from utils.kb import main_review
from aiogram.filters import Command


router = Router()

@router.message(Command("review"), IsBan(), IsPrivate())
async def variable_review(message: types.Message):
    await message.answer(Message.REVIEW_VARIBLE, reply_markup=main_review.as_markup())


    