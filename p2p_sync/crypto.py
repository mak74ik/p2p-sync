import os
from cryptography.fernet import Fernet

class SyncCrypto:
    """Handles symmetric encryption and decryption for file chunks and protocol messages."""

    def __init__(self, key: bytes = None):
        if key is None:
            self.key = Fernet.generate_key()
        else:
            if isinstance(key, str):
                key = key.encode("utf-8")
            self.key = key
        self.fernet = Fernet(self.key)

    @classmethod
    def generate_new_key(cls) -> str:
        """Generates a base64-encoded 256-bit Fernet key."""
        return Fernet.generate_key().decode("utf-8")

    def encrypt(self, data: bytes) -> bytes:
        """Encrypts data with authenticated encryption (HMAC-SHA256 + AES-128-CBC)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypts and verifies data integrity."""
        return self.fernet.decrypt(token)
