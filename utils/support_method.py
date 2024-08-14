from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_pagination_keyboard(page: int, callback_name_left="prev_", callback_name_right="next_"):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"{callback_name_left}{page}"),
                InlineKeyboardButton(text="➡️", callback_data=f"{callback_name_right}{page}"))
    return keyboard

def can_convert_to_float(s) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False

async def generate_promo_code(message: Message) -> str:
    referral_link = f"https://t.me/WebPegasConfig_bot?start={message.from_user.id}"
    return referral_link