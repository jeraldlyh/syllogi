from cryptography.fernet import Fernet

from lib.env import get_environment_variable


def _derive_key(secret: str) -> bytes:
    """Derive a Fernet-compatible key from a secret string."""
    import hashlib

    return hashlib.sha256(secret.encode()).digest()


def encrypt(plaintext: str) -> str:
    """Encrypt a string, return ciphertext as string."""

    secret = str(get_environment_variable("AUTH_SECRET_KEY", ignore_error=False))
    key = _derive_key(secret)
    fernet = Fernet(key)
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext string, return plaintext."""

    secret = str(get_environment_variable("AUTH_SECRET_KEY", ignore_error=False))
    key = _derive_key(secret)
    fernet = Fernet(key)
    return fernet.decrypt(ciphertext.encode()).decode()
