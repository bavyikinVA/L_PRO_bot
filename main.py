from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from fastapi.staticfiles import StaticFiles
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse


from bot.create_bot import dp, bot, stop_bot, start_bot
from api.router import api_router
from config import settings
from database.database import async_session_maker
from services.reminder_service import ReminderService
from core.rate_limit import limiter

async def send_admin_msg(client, text):
    for admin in settings.ADMIN_IDS:
        try:
            await client.post(f"{settings.get_tg_api_url()}/sendMessage",
                              json={"chat_id": admin, "text": text, "parse_mode": "HTML"})
        except Exception as E:
            logger.exception(f"Ошибка при отправке сообщения админу: {E}")


@asynccontextmanager
async def lifespan(app):
    logger.info("Starting bot setup...")
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    logger.info(f"Webhook set to {webhook_url}")
    async with async_session_maker() as session:
        restored = await ReminderService.recover_queue(session)
        logger.info(f"Очередь напоминаний восстановлена. Задач: {restored}")
    yield
    logger.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logger.info("Webhook deleted")


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory='static'), name='static')

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Слишком много запросов. Попробуйте позже."
        },
    )

app.include_router(api_router)

allowed_origins = settings.get_allowed_origins()

cors_kwargs = {
    "allow_origins": allowed_origins,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Content-Type",
        "Authorization",
        "X-Telegram-Init-Data",
    ],
}

if settings.ENVIRONMENT == "dev":
    cors_kwargs["allow_origin_regex"] = r"https://.*\.ngrok-free\.app"

app.add_middleware(CORSMiddleware, **cors_kwargs)


@app.post("/webhook/{secret}")
@limiter.limit("60/minute")
async def webhook(secret: str, request: Request):
    if secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info("Received webhook request")

    try:
        update = Update.model_validate(
            await request.json(),
            context={"bot": bot}
        )

        async with async_session_maker() as session:
            await dp.feed_update(bot, update, session=session)

        logger.info("Update processed")

    except TelegramBadRequest as e:
        error_text = str(e).lower()

        if "query is too old" in error_text or "query id is invalid" in error_text:
            logger.warning(f"Старый callback Telegram проигнорирован: {e}")
        else:
            logger.exception(f"TelegramBadRequest при обработке webhook: {e}")

    except Exception as e:
        logger.exception(f"Ошибка при обработке webhook: {e}")

    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}