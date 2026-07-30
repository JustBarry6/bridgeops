from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import settings


@lru_cache
def _get_fernet() -> Fernet:
    return Fernet(settings.fernet_key.encode())


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()