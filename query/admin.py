from aiogram import types, Router, F
import aiogram
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from message import Message
from aiogram.fsm.context import FSMContext
from utils.custom_filter import IsPrivate, IsSuperAdmin
from utils.database.database import database as db_manager
from utils.forms import AdminUsernameForms, AdminAddMoneyDist
from utils.kb import main_admin
from utils.database.models import UserRequest, User
from config import logger


router = Router()

@router.callback_query(F.data == "in_processing_order")
async def show_in_processing_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_admin=1, order_type="В обработке", message_id=callback_query.message.message_id)
    await display_request_page(callback_query, state)

@router.callback_query(F.data == "active_order")
async def show_active_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_admin=1, order_type="В разработке", message_id=callback_query.message.message_id)
    await display_request_page(callback_query, state)

@router.callback_query(F.data == "access_order")
async def show_close_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_admin=1, order_type="Выполнен", message_id=callback_query.message.message_id)
    await display_request_page(callback_query, state)

@router.callback_query(F.data == "cancel_order")
async def show_cancel_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_admin=1, order_type="Отменённый", message_id=callback_query.message.message_id)
    await display_request_page(callback_query, state)

@router.callback_query(F.data == "fail_order")
async def show_fail_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_admin=1, order_type="Расторгнут", message_id=callback_query.message.message_id)
    await display_request_page(callback_query, state)

@router.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def handle_pagination(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("page_admin", 1)
    order_type = data.get("order_type", "В обработке")
    action, _ = callback_query.data.split("_")

    if action == "prev":
        current_page -= 1
    elif action == "next":
        current_page += 1
    if current_page == 0:
        message_id = data.get("message_id")
        await callback_query.bot.edit_message_reply_markup(
                    chat_id=callback_query.message.chat.id,
                    message_id=message_id,
                    reply_markup=main_admin.as_markup()
            )
        await callback_query.message.answer(Message.END_LIST)
        await state.clear()
        return
    await state.update_data(page_admin=current_page, order_type=order_type)
    await display_request_page(callback_query, state)

async def display_request_page(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("page_admin", 1)
    order_type = data.get("order_type", "В обработке")
    message_id = data.get("message_id")

    async for session in db_manager.get_session():
        user = await User.find_user_by_telegram_id(session, callback_query.from_user.id)
        request: UserRequest = await UserRequest.find_requests_all(session, user.id, page, order_type)

        if request:
            await state.update_data(current_request_id=request.id)
            text = f"{request.request_date}: {request.direction} - {request.description}\nСтатус: {request.status}"
            if request.file_id:
                if message_id:
                    try:
                        await callback_query.bot.edit_message_media(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            media=types.InputMediaDocument(media=request.file_id, caption=text),
                            reply_markup=create_order_keyboard(order_type, page).as_markup()
                        )
                    except aiogram.exceptions.TelegramBadRequest:
                        await callback_query.bot.edit_message_reply_markup(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            reply_markup=None
                        )
                        new_message = await callback_query.message.answer_document(document=request.file_id, caption=text, reply_markup=create_order_keyboard(order_type, page).as_markup())
                        await state.update_data(message_id=new_message.message_id)
                else:
                    new_message = await callback_query.message.answer_document(document=request.file_id, caption=text, reply_markup=create_order_keyboard(order_type, page).as_markup())
                    await state.update_data(message_id=new_message.message_id)
            else:
                if message_id:
                    try:
                        await callback_query.bot.edit_message_text(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            text=text,
                            reply_markup=create_order_keyboard(order_type, page).as_markup()
                        )
                    except aiogram.exceptions.TelegramBadRequest:
                        await callback_query.bot.edit_message_reply_markup(
                            chat_id=callback_query.message.chat.id,
                            message_id=message_id,
                            reply_markup=None
                        )
                        new_message = await callback_query.message.answer(text, reply_markup=create_order_keyboard(order_type, page).as_markup())
                        await state.update_data(message_id=new_message.message_id)
                else:
                    new_message = await callback_query.message.answer(text, reply_markup=create_order_keyboard(order_type, page).as_markup())
                    await state.update_data(message_id=new_message.message_id)
        else:
            if message_id:
                await callback_query.bot.edit_message_reply_markup(
                    chat_id=callback_query.message.chat.id,
                    message_id=message_id,
                    reply_markup=main_admin.as_markup()
                )
            else:
                await callback_query.message.answer(Message.END_LIST)
            await state.clear()

        await session.commit()

def create_order_keyboard(order_type: str, page: int) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    if order_type == "В обработке":
        keyboard.row(
            InlineKeyboardButton(text="Принять в работу", callback_data="accept_order_in_work"),
            InlineKeyboardButton(text="Отменить", callback_data="cancel_order")
        )
    elif order_type == "В разработке":
        keyboard.row(
            InlineKeyboardButton(text="Расторжение", callback_data="terminate_order"),
            InlineKeyboardButton(text="Принятие", callback_data="accept_order")
        )
    keyboard.row(
        InlineKeyboardButton(text="⬅️", callback_data=f"prev_{page}"),
        InlineKeyboardButton(text="➡️", callback_data=f"next_{page}")
    )
    return keyboard

@router.callback_query(F.data == "accept_order_in_work")
async def accept_order_in_work(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    request_id = data.get("current_request_id")
    
    if request_id:
        async for session in db_manager.get_session():
            user: User = await UserRequest.get_distributor_for_request(session, request_id)
            logger.info(user)
            if user:
                await UserRequest.update_by_id(session=session, request_id=request_id, user_id=callback_query.from_user.id, status="В разработке")
                await callback_query.message.answer(f"Заказ {request_id} принят в разработку.")
            else:
                await callback_query.message.answer("Ошибка: информация о дистрибьюторе или пользователе не найдена")
            await session.commit()
    else:
        await callback_query.message.answer(Message.ERROR_INDEF_ORDER)
    await state.clear()
    
    await state.update_data(telegram_id=user.telegram_id)
    await callback_query.message.answer(Message.INPUT_MONEY)
    await state.set_state(AdminAddMoneyDist.money)

@router.callback_query(F.data == "accept_order")
async def accept_order(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    request_id = data.get("current_request_id")
    if request_id:
        async for session in db_manager.get_session():
            async with session.begin():
                await UserRequest.update_by_id(session=session, request_id=request_id, user_id=callback_query.from_user.id, status="Выполнен")
            await session.commit()

        await callback_query.message.answer(f"Заказ {request_id} выполнен")
    else:
        await callback_query.message.answer(Message.ERROR_INDEF_ORDER)
    await state.clear()

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    request_id = data.get("current_request_id")
    if request_id:
        async for session in db_manager.get_session():
            async with session.begin():
                await UserRequest.update_by_id(session=session, request_id=request_id, user_id=callback_query.from_user.id, status="Отменённый", )
            await session.commit()
        await callback_query.message.answer(f"Заказ {request_id} отменён")
    else:
        await callback_query.message.answer(Message.ERROR_INDEF_ORDER)
    await state.clear()

@router.callback_query(F.data == "terminate_order")
async def terminate_order(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    request_id = data.get("current_request_id")
    if request_id:
        async for session in db_manager.get_session():
            async with session.begin():
                await UserRequest.update_by_id(session=session, request_id=request_id, user_id=callback_query.from_user.id, status="Расторгнут")
            await session.commit()
        await callback_query.message.answer(f"Заказ {request_id} расторгнут")
    else:
        await callback_query.message.answer(Message.ERROR_INDEF_ORDER)
    await state.clear()

@router.callback_query(F.data == "add_admin", IsPrivate(), IsSuperAdmin())
async def process_add_admin(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(Message.SUPER_ADMIN)
    await state.update_data(ban_user=False)
    await state.set_state(AdminUsernameForms.username)

@router.callback_query(F.data == "ban_user", IsPrivate(), IsSuperAdmin())
async def process_ban_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(Message.SUPER_ADMIN_BAN_USER)
    await state.update_data(ban_user=True)
    await state.set_state(AdminUsernameForms.username)
