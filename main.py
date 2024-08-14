import asyncio
import logging
import signal
from aiogram import Bot, Dispatcher
from handlers import routers
from query import routers as routers_query
from utils.database.database import database as db_manager
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from config import *
from aiogram import Bot, Dispatcher
from middlewares import middleware


bot = Bot(token=TOKEN)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        logger.log(level, record.getMessage())

logging.getLogger('aiogram').setLevel(logging.DEBUG)
logging.getLogger('aiogram').addHandler(InterceptHandler())
logging.getLogger('asyncio').setLevel(logging.DEBUG)
logging.getLogger('asyncio').addHandler(InterceptHandler())

dp = Dispatcher(storage=MemoryStorage())

for router in routers:
    dp.include_router(router)

for router in routers_query:
    dp.include_router(router)
dp.message.middleware(middleware["AntiSpam"]())


async def setup_bot_commands():
    logger.info("Initializing database models")
    # await db_manager.init_models()
    logger.info("Database models initialized")
    bot_commands = [
        BotCommand(command="/start", description="Запустить бота 🚀"),
        BotCommand(command="/cancel", description="Отмена ввода 🚫"),
        BotCommand(command="/review", description="Оставить отзыв 📝"),
        BotCommand(command="/dist", description="Дистрибьютер 📦"),
        BotCommand(command="/user", description="Клиент 👤")
    ]
    await bot.set_my_commands(bot_commands)
    logger.info("Bot commands set up successfully")


async def main():
    await setup_bot_commands()
    await dp.start_polling(bot)


def shutdown(signal, frame):
    logger.info("Received SIGINT, shutting down...")
    asyncio.create_task(dp.stop_polling())
    asyncio.create_task(db_manager.close())
    asyncio.get_event_loop().stop()

signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    asyncio.run(main())