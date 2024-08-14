from loguru import logger
from dotenv import load_dotenv
import os


logger.add("log.log", format="{time} {level} {message}", level="INFO", rotation="100 MB", compression="zip", enqueue=True)
load_dotenv()

TOKEN = os.getenv('TOKEN')
PG_LINK = os.getenv('PG_LINK')
CHAT_ID = int(os.getenv('CHAT_ID'))