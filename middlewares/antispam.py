from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Any

from cachetools import TTLCache
from message import Message as MessageText


class AntiFloodMiddleware(BaseMiddleware):

    def __init__(self, timelimit: int=3) -> None:
        self.limit = TTLCache(maxsize=10000, ttl=timelimit)

    async def __call__(self, handler, event: Message, data: dict[str, Any]) -> Any:
        if event.chat.id in self.limit:
            await event.answer(MessageText.ANTI_SPAM)
            return
        else:
            self.limit[event.chat.id] = None
        return await handler(event, data)