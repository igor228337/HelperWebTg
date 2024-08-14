from aiogram import types, Router
from message import Message
from utils.custom_filter import IsBan, IsPrivate
from utils.forms import ReviewData
from utils.kb import main_rating_review, cancel
from aiogram.fsm.context import FSMContext


router = Router()

@router.message(ReviewData.title, IsBan(), IsPrivate())
async def process_set_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(Message.REVIEW_SET_DESCRIPTION, reply_markup=cancel.as_markup())
    await state.set_state(ReviewData.description)

@router.message(ReviewData.description, IsBan(), IsPrivate())
async def process_set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(Message.REVIEW_SET_RATING, reply_markup=main_rating_review.as_markup())