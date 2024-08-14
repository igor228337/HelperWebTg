from aiogram import types, Router, F
from message import Message
from aiogram.fsm.context import FSMContext
from utils.database.database import database as db_manager
from utils.support_method import generate_promo_code
from utils.kb import main_dist

from utils.database.models import User, PromoCode, Distributor
from config import logger

router = Router()

@router.callback_query(F.data == "gen_promo")
async def process_callback_generate_promo(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    promo = await generate_promo_code(callback_query)
    async for session in db_manager.get_session():
        user = await User.find_user_by_telegram_id(session, callback_query.from_user.id)
        if user:
            distributor = Distributor(user_id=user.id)
            session.add(distributor)
            await session.flush()
            logger.info(distributor.id)
            promo_code = PromoCode(code=promo, distributor_id=distributor.id)
            session.add(promo_code)
            await callback_query.message.answer(Message.PROMO.format(promo), reply_markup=main_dist.as_markup())
        await session.commit()
        
@router.callback_query(F.data == "get_promo")
async def process_callback_get_promo(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    async for session in db_manager.get_session():
        dist = await Distributor.find_distributor_by_telegram_id(session, callback_query.from_user.id)
        promo_codes = await Distributor.find_promo_codes_by_distributor_id(session, dist.id)
        await session.commit()
        await callback_query.message.answer(Message.PROMO.format(promo_codes[0].code), reply_markup=main_dist.as_markup())