import asyncio
import logging
import signal
from aiogram import Bot, Dispatcher
from handlers import routers
from query import routers as routers_query
from utils.database.database import database as db_manager
from aiogram.types import BotCommand, FSInputFile
from config import *
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from aiogram.fsm.storage.redis import RedisStorage
import uvicorn
from contextlib import asynccontextmanager
import redis
from middlewares import middleware


WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8080
WEBHOOK_PATH = "/webhook"
BASE_WEBHOOK_URL = "https://enabling-magpie-stunning.ngrok-free.app"


bot = Bot(token=TOKEN)

async def start_bot():
    logger.info("Initializing database models")  
    # await db_manager.init_models()
    logger.info("Database models initialized")
    bot_commands = [
        BotCommand(command="/start", description="Запустить бота \U0001F680"),
        BotCommand(command="/cancel", description="Отмена ввода \U0001F6AB"),
        BotCommand(command="/review", description="Оставить отзыв \U0001F4DD"),
        BotCommand(command="/dist", description="Дистрибьютер \U0001F4E6"),
        BotCommand(command="/user", description="Клиент \U0001F464")
    ]
    await bot.set_my_commands(bot_commands)
    logger.info("Bot commands set up successfully")

storage = RedisStorage.from_url('redis://localhost:6379/0')
dp = Dispatcher(storage=storage)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_bot()
    # await db_manager.init_models()
    url_webhook = BASE_WEBHOOK_URL+WEBHOOK_PATH
    await bot.set_webhook(url=url_webhook,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    yield
    await db_manager.close()
    await bot.delete_webhook()

class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        logger.log(level, record.getMessage())

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.getLogger('aiogram').setLevel(logging.DEBUG)
logging.getLogger('aiogram').addHandler(InterceptHandler())
logging.getLogger('asyncio').setLevel(logging.DEBUG)
logging.getLogger('asyncio').addHandler(InterceptHandler())



for router in routers:
    dp.include_router(router)

for router in routers_query:
    dp.include_router(router)
dp.message.middleware(middleware["AntiSpam"]())

@app.get("/")
async def index(request: Request):
    return {200: "Я кому сказал, съебались нахуй от сюда в ужасе"}


@app.post(WEBHOOK_PATH)
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)

async def check_webhook():
    webhook_info = await bot.get_webhook_info()
    logger.info(webhook_info)


def shutdown(signal, frame):
    logger.info("Received SIGINT, shutting down...")

signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    uvicorn.run(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
