from aiogram import types

async def generate_promo_code(message: types.Message) -> str:
    referral_link = f"https://t.me/WebPegasConfig_bot?start={message.from_user.id}"
    return referral_link