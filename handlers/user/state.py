from aiogram import types, Router, F
from message import Message
from aiogram.fsm.context import FSMContext
from utils.custom_filter import IsBan
from utils.database.database import database as db_manager
from utils.forms import UserRequests
from utils.database.models import User, UserRequest
from utils.kb import main_user, greet_kb, cancel
from config import CHAT_ID


router = Router()

@router.message(UserRequests.direction, IsBan())
async def process_direction(message: types.Message, state: FSMContext):
    await state.update_data(direction=message.text)
    await state.set_state(UserRequests.description)
    await message.answer(Message.DESCRIPTION_ORDER, reply_markup=cancel.as_markup())

@router.message(UserRequests.description, IsBan())
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(UserRequests.file_path)
    await message.answer(Message.FILE_TE, reply_markup=greet_kb.as_markup())

@router.message(UserRequests.file_path, F.document, IsBan())
async def process_file(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    file_id = message.document.file_id
    await state.update_data(file_id=file_id)

    direction = user_data['direction']
    description = user_data['description']

    await message.answer(Message.LAST_VIEW.format(direction, description, "В обработке"), reply_markup=main_user.as_markup())
    
    async for session in db_manager.get_session():
        user_id = await User.find_user_by_telegram_id(session, message.from_user.id)
        await message.bot.send_document(chat_id=CHAT_ID, caption=Message.LAST_VIEW.format(direction, description, "В обработке"), document=file_id)
        order = UserRequest(user_id=user_id.id, direction=direction, description=description, file_id=file_id)
        session.add(order)
        await session.commit()

    await state.clear()