from aiogram import types, Router, F
from message import Message
from aiogram.fsm.context import FSMContext
from utils.database.database import database as db_manager
from utils.forms import PromocodeUser
from utils.kb import generate_promo, main_dist, no_promo, main_user
from utils.database.models import Distributor, PromoCode, UserPromoCodeUsage

router = Router()


@router.callback_query(F.data == "distributor")
async def process_callback_distributor(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    async for session in db_manager.get_session():
        if await Distributor.find_distributor_by_telegram_id(session, callback_query.from_user.id):
            await callback_query.message.answer(Message.ACTION_DIST, reply_markup=main_dist.as_markup())
        else:
            await callback_query.message.answer(Message.GENERATE_PROMO, reply_markup=generate_promo.as_markup())
        await session.commit()


@router.callback_query(F.data == "user")
async def process_callback_sign_up_order(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer(Message.ACTION_DIST, reply_markup=main_user.as_markup())

