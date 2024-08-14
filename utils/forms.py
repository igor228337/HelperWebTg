from aiogram.fsm.state import StatesGroup, State

class PromocodeUser(StatesGroup):
    promo = State()

class UserRequests(StatesGroup):
    direction = State()
    description = State()
    file_path = State()

class AdminUsernameForms(StatesGroup):
    username = State()

class AdminAddMoneyDist(StatesGroup):
    money = State()

class ReviewData(StatesGroup):
    title = State()
    description = State()
    rating = State()