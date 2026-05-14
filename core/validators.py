import re
import phonenumbers
from fastapi import HTTPException


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None

    raw = phone.strip()

    try:
        parsed = phonenumbers.parse(raw, "RU")
    except phonenumbers.NumberParseException:
        raise HTTPException(status_code=400, detail="Некорректный номер телефона")

    if not phonenumbers.is_valid_number(parsed):
        raise HTTPException(status_code=400, detail="Некорректный номер телефона")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def validate_name(value: str | None, field_name: str) -> str | None:
    value = normalize_text(value)

    if value is None:
        return value

    if len(value) > 80:
        raise HTTPException(status_code=400, detail=f"{field_name} слишком длинное")

    if not re.fullmatch(r"[А-Яа-яЁёA-Za-z\-\s]+", value):
        raise HTTPException(status_code=400, detail=f"{field_name} содержит недопустимые символы")

    return value