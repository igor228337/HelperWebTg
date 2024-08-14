from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from utils.custom_filter import IsBan, IsPrivate, IsAdmin, IsSuperAdmin, IsFloat
from utils.forms import AdminUsernameForms, AdminAddMoneyDist
from utils.kb import main_admin
from utils.database.database import database as db_manager
from utils.database.models import User, Distributor
from utils.support_method import can_convert_to_float
from message import Message


router = Router()

@router.message(AdminUsernameForms.username, IsPrivate(), IsSuperAdmin())
async def add_admin_proccess(message: types.Message, state: FSMContext):
    get_data = await state.get_data()
    username = message.text
    ban_user = get_data.get("ban_user")
    if not ban_user:
        async for session in db_manager.get_session():
            add = await User.make_admin_by_username(session, username)
            await message.answer(Message.ADD_ADMIN, reply_markup=main_admin.as_markup()) if add else await message.answer(Message.FAIL_ADD_ADMIN, reply_markup=main_admin.as_markup())
            await session.commit()
    else:
        if can_convert_to_float(username):
            async for session in db_manager.get_session():
                user: User = await User.find_user_by_telegram_id(session, int(username))
                user.is_ban = True
                await session.commit()
        else:
            async for session in db_manager.get_session():
                user: User = await User.find_user_by_telegram_username(session, username)
                user.is_ban = True
                await session.commit()
        await message.answer(Message.ACESS_BAN, reply_markup=main_admin.as_markup())
    await state.clear()
        
@router.message(AdminAddMoneyDist.money, IsPrivate(), IsSuperAdmin(), IsFloat(), IsBan())
async def process_add_money_money(message: types.Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = data.get("telegram_id")
    money = float(message.text)
    async for session in db_manager.get_session():
        result = await Distributor.add_minus_money_dist(session=session, telegram_id=telegram_id, money=money)
        await session.commit()
    if result:
        if money >= 0:
            await message.answer(Message.ADD_MONEY_SUCCESS, reply_markup=main_admin.as_markup())
        else:
            await message.answer(Message.MINUS_MONEY_SUCCESS, reply_markup=main_admin.as_markup())
    else:
        await message.answer(Message.NO_MONEY, reply_markup=main_admin.as_markup())
    
    await state.clear()