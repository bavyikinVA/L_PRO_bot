import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

from config import settings


MAX_INIT_DATA_AGE_SECONDS = 24 * 60 * 60  # 24 часа

def verify_telegram_init_data(init_data: str) -> dict:
    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed_data.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Нет hash в initData"
        )
    auth_date = parsed_data.get("auth_date")
    if not auth_date:
        raise HTTPException(
            status_code=401,
            detail="Нет auth_date"
        )
    try:
        auth_timestamp = int(auth_date)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Некорректный auth_date"
        )

    current_timestamp = int(time.time())
    if current_timestamp - auth_timestamp > MAX_INIT_DATA_AGE_SECONDS:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData устарел"
        )
    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.BOT_TOKEN.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=401,
            detail="Неверная подпись Telegram"
        )

    user_raw = parsed_data.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=401,
            detail="Нет данных пользователя"
        )

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=401,
            detail="Некорректный JSON user"
        )
    return user


async def require_admin(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data")):
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="Нет Telegram initData"
        )

    user = verify_telegram_init_data(x_telegram_init_data)
    telegram_id = user.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=401,
            detail="Нет Telegram ID"
        )

    if int(telegram_id) not in settings.ADMIN_IDS:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён"
        )

    return user