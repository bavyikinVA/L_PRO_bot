from loguru import logger
from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Any, Dict
from aiogram.types import TelegramObject
from database.database import async_session_maker


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            try:
                data["db"] = session
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                raise