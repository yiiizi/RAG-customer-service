"""
Encryption utilities for sensitive data like API keys.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from config.settings import settings


def _get_fernet_key() -> bytes:
    """Derive a Fernet key from the JWT secret key."""
    salt = b"rag_system_salt"  # Fixed salt for deterministic key derivation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.JWT_SECRET_KEY.encode()))
    return key


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key."""
    if not api_key:
        return ""
    
    fernet = Fernet(_get_fernet_key())
    encrypted = fernet.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_api_key: str) -> str:
    """Decrypt an API key."""
    if not encrypted_api_key:
        return ""
    
    fernet = Fernet(_get_fernet_key())
    decrypted = fernet.decrypt(base64.urlsafe_b64decode(encrypted_api_key))
    return decrypted.decode()
