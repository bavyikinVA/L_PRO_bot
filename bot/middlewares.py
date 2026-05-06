from loguru import logger
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
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

            except TelegramBadRequest as e:
                await session.rollback()

                error_text = str(e).lower()

                if "query is too old" in error_text or "query id is invalid" in error_text:
                    logger.warning(f"Старый callback Telegram проигнорирован: {e}")
                    return None

                logger.exception(e)
                raise

            except Exception as e:
                logger.exception(e)
                await session.rollback()
                raise