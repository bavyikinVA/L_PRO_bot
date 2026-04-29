from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from fastapi.staticfiles import StaticFiles
from aiogram.types import Update

from bot.create_bot import dp, bot, stop_bot, start_bot
from api.router import api_router
from config import settings
from database.database import async_session_maker


async def send_admin_msg(client, text):
    for admin in settings.ADMIN_IDS:
        try:
            await client.post(f"{settings.get_tg_api_url()}/sendMessage",
                              json={"chat_id": admin, "text": text, "parse_mode": "HTML"})
        except Exception as E:
            logger.exception(f"Ошибка при отправке сообщения админу: {E}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bot setup...")
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    logger.info(f"Webhook set to {webhook_url}")
    yield
    logger.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logger.info("Webhook deleted")


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory='static'), name='static')

# Подключаем API роутеры
app.include_router(api_router)

# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",
                   "http://frontend:3000",
                   "http://localhost:3000"
                   ],  # для docker,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook")
async def webhook(request: Request) -> None:
    logger.info("Received webhook request")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    async with async_session_maker() as session:
        await dp.feed_update(bot, update, session=session)
    logger.info("Update processed")


@app.get("/check")
async def check():
    return {"status": "ok", "bot": str(bot)}