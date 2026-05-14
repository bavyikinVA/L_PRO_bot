import hashlib
from cryptography.fernet import Fernet, InvalidToken

from config import settings


class EncryptionService:
    def __init__(self) -> None:
        self.fernet = Fernet(settings.FERNET_SECRET_KEY.encode())

    def encrypt(self, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str | None) -> str | None:
        if value is None or value == "":
            return value

        try:
            return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return value


encryption_service = EncryptionService()

def make_hash(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()