import aiogram
from aiogram import types, Router, F
from aiogram.types import CallbackQuery
from config import CHAT_ID
from message import Message
from aiogram.fsm.context import FSMContext
from utils.database.database import database as db_manager
from utils.kb import main_user, cancel
from utils.database.models import UserRequest, User
from utils.forms import UserRequests
from utils.support_method import create_pagination_keyboard
from config import *

router = Router()

user_name = "user"
user_left = user_name + "|left_"
user_right = user_name + "|right_"

@router.callback_query(F.data == "history")
async def show_request_history(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_user=1, message_id=callback_query.message.message_id)
    await display_request_page(callback_query, state)

@router.callback_query(F.data.startswith(user_left) | F.data.startswith(user_right))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("page_user", 1)
    action, _ = callback_query.data.split("_")

    if action + "_" == user_left:
        current_page -= 1
    elif action + "_" == user_right:
        current_page += 1
    
    if current_page == 0:
        message_id = data.get("message_id")
        await callback_query.bot.edit_message_reply_markup(
                    chat_id=callback_query.message.chat.id,
                    message_id=message_id,
                    reply_markup=main_user.as_markup()
            )
        await callback_query.message.answer(Message.END_LIST)
        await state.clear()
        return
    
    await state.update_data(page_user=current_page)
    await display_request_page(callback_query, state)

async def display_request_page(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("page_user", 1)
    message_id = data.get("message_id")

    async for session in db_manager.get_session():
        user = await User.find_user_by_telegram_id(session, callback_query.from_user.id)
        if user is None:
            request = None
        else:
            request: UserRequest = await UserRequest.find_requests_all(session, user.id, page)

        if request:
            text = (f"📅 {request.request_date}:\n🔍 {request.direction}\n🔄 {request.description}\n🟢 Статус: {request.status}")

            if request.status == "Выполнен":
                text += " ✅"
            elif request.status == "В разработке":
                text += " 🔄"
            elif request.status == "Отменённый":
                text += " ❌"
            else:
                text += " ❓"
            if request.file_id:
                if message_id:
                    try:
                        await callback_query.bot.edit_message_media(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            media=types.InputMediaDocument(media=request.file_id, caption=text),
                            reply_markup=create_pagination_keyboard(page, user_left, user_right).as_markup()
                        )
                    except aiogram.exceptions.TelegramBadRequest:
                        await callback_query.bot.edit_message_reply_markup(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            reply_markup=None
                        )
                        new_message = await callback_query.message.answer_document(document=request.file_id, caption=text, reply_markup=create_pagination_keyboard(page, user_left, user_right).as_markup())
                        await state.update_data(message_id=new_message.message_id)
                else:
                    new_message = await callback_query.message.answer_document(document=request.file_id, caption=text, reply_markup=create_pagination_keyboard(page, user_left, user_right).as_markup())
                    await state.update_data(message_id=new_message.message_id)
            else:
                if message_id:
                    try:
                        await callback_query.bot.edit_message_text(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            text=text,
                            reply_markup=create_pagination_keyboard(page, user_left, user_right).as_markup()
                        )
                    except aiogram.exceptions.TelegramBadRequest:
                        await callback_query.bot.edit_message_reply_markup(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            reply_markup=None
                        )
                        new_message = await callback_query.message.answer(text, reply_markup=create_pagination_keyboard(page, user_left, user_right).as_markup())
                        await state.update_data(message_id=new_message.message_id)
                else:
                    new_message = await callback_query.message.answer(text, reply_markup=create_pagination_keyboard(page, user_left, user_right).as_markup())
                    await state.update_data(message_id=new_message.message_id)
        else:
            if message_id:
                await callback_query.bot.edit_message_text(
                    text=Message.ACTION_DIST,
                    chat_id=callback_query.message.chat.id,
                    message_id=message_id,
                    reply_markup=main_user.as_markup()
                )
            else:
                await callback_query.message.answer(Message.END_LIST)
            await state.clear()
        await session.commit()


@router.callback_query(F.data == "order")
async def process_callback_order(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(Message.NAME_DIRECTION, reply_markup=cancel.as_markup())
    await state.set_state(UserRequests.direction)

@router.callback_query(F.data == "help")
async def process_callback_order(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(Message.HELP, reply_markup=main_user.as_markup())

@router.callback_query(F.data == "no_file")
async def process_file(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    user_data = await state.get_data()

    direction = user_data['direction']
    description = user_data['description']
    
    async for session in db_manager.get_session():
        user_id = await User.find_user_by_telegram_id(session, call.from_user.id)
        await call.message.bot.send_message(chat_id=CHAT_ID, text=Message.LAST_VIEW.format(direction, description, "В обработке"))
        order = UserRequest(user_id=user_id.id, direction=direction, description=description)
        session.add(order)
        await session.commit()

    await call.message.answer(Message.LAST_VIEW.format(direction, description, "В обработке"), reply_markup=main_user.as_markup())
    await state.clear()
