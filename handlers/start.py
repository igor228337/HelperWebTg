from aiogram import types, Router, F
from message import Message
from aiogram.filters import Command, CommandStart
from utils.custom_filter import IsBan, IsPrivate, IsGroup
from utils.kb import main_kb
from utils.database.database import database as db_manager
from utils.database.models import PromoCode, User, UserPromoCodeUsage
from aiogram.fsm.context import FSMContext
from config import logger

router = Router()

@router.message(CommandStart(), IsGroup(), IsBan())
async def send_id(message: types.Message):
    await message.answer(f"Ваш id: {message.chat.id}")


@router.message(CommandStart(), IsPrivate(), IsBan())
async def send_welcome(message: types.Message):
    if len(message.text.split(" ")) != 2:
        promo_code = f"https://t.me/WebPegasConfig_bot?start=6044110141"
    else: 
        promo_code = f"https://t.me/WebPegasConfig_bot?start={message.text.split(' ')[-1]}"
        logger.warning(promo_code)
    telegram_id = int(message.from_user.id)
    user_username = message.from_user.username
    async for session in db_manager.get_session():
        if await User.is_user_registered(session, telegram_id):
            promo_code_id = await PromoCode.find_by_code(session, promo_code)
            logger.warning(promo_code_id)
        else:
            user = User(telegram_id=telegram_id, username=user_username)
            session.add(user)
            await session.flush()
            promo_code_id = await PromoCode.find_by_code(session, promo_code)
            logger.info(promo_code_id)
            if promo_code_id is not None:
                user_promo = UserPromoCodeUsage(user_id=user.id, promo_code_id=promo_code_id)
                session.add(user_promo)
        await message.answer(Message.START, reply_markup=main_kb.as_markup())
        await session.commit()
        

@router.message(Command("cancel"), IsPrivate(), IsBan())
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(Message.NO_ACTION)
        return

    await state.clear()
    await message.answer(Message.YES_ACTION_CANCLE)
    await message.answer(Message.START, reply_markup=main_kb.as_markup())
        

@router.callback_query(F.data == "cancel")
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    current_state = await state.get_state()
    if current_state is None:
        await callback_query.message.answer(Message.NO_ACTION)
        return

    await state.clear()
    await callback_query.message.answer(Message.YES_ACTION_CANCLE)
    await callback_query.message.answer(Message.START, reply_markup=main_kb.as_markup())