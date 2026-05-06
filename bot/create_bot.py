from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from config import settings
from bot.handlers import user
# from bot.handlers import admin
from bot.middlewares import DBSessionMiddleware

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.update.middleware(DBSessionMiddleware())

dp.include_router(user.router)
# dp.include_router(admin.router)

async def start_bot():
    try:
        for num in range(len(settings.ADMIN_IDS)):
            await bot.send_message(settings.ADMIN_IDS[num], f'Бот запущен🥳.')
    except Exception as e:
        logger.exception(e)

async def stop_bot():
    try:
        for num in range(len(settings.ADMIN_IDS)):
            await bot.send_message(settings.ADMIN_IDS[num], 'Бот остановлен😔.')
        await bot.session.close()
    except Exception as e:
        logger.exception(e)