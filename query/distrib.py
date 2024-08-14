from aiogram import types, Router, F
from message import Message
from aiogram.fsm.context import FSMContext
from utils.database.database import database as db_manager
from utils.kb import main_dist, output_money

from utils.database.models import Distributor, UserPromoCodeUsage
from aiogram.enums.parse_mode import ParseMode

router = Router()

@router.callback_query(F.data == "balance_dist")
async def process_callback_get_balance(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    async for session in db_manager.get_session():
        distr = await Distributor.find_distributor_by_telegram_id(session, callback_query.from_user.id)
        await session.commit()
    if distr.balance >= 1000.0:
        await callback_query.message.answer(Message.BALANCE.format(distr.balance), reply_markup=output_money.as_markup())
    else:
        await callback_query.message.answer(Message.BALANCE.format(distr.balance), reply_markup=main_dist.as_markup())

@router.callback_query(F.data == "output_money")
async def process_callback_output_money(callback: types.CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await callback.message.answer(Message.OUTPUT_MONEY, reply_markup=main_dist.as_markup())

@router.callback_query(F.data == "statistic_dist")
async def process_callback_get_statistic(callback: types.CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    async for session in db_manager.get_session():
        distributor = await Distributor.find_distributor_by_telegram_id(session, callback.from_user.id)
        if distributor is None:
            await session.commit()
            await callback.message.answer(Message.NO_DISTRIB, reply_markup=main_dist.as_markup())
            return

        count_user = await UserPromoCodeUsage.count_referrals_for_distributor(session, distributor.id)
        if not count_user:
            count_user = 0
        statistics = await Distributor.get_order_statistics(session, distributor.id)
        if not statistics:
            await session.commit()
            
            await callback.message.answer(Message.NO_STATISTICS + f"\n{Message.COUNT_USER}{count_user}", reply_markup=main_dist.as_markup())
            return
        stats_message = "Статистика по заказам ваших приглашённых:\n"
        for status, count in statistics.items():
            stats_message += f"• {status}: {count}\n"
        stats_message += f"{Message.COUNT_USER}{count_user}"
        await callback.message.reply(stats_message, parse_mode=ParseMode.MARKDOWN, reply_markup=main_dist.as_markup())
        await session.commit()