import base64
import os
from cryptography.fernet import Fernet
from app.core.config import settings


class BiometricEncryptionHelper:
    """Application-level biometric template encryption helper (AGENTS.md Rule 5).
    Guarantees raw fingerprint templates are NEVER stored in plaintext in the database.
    """

    def __init__(self, key: str | None = None):
        raw_key = key or settings.BIOMETRIC_ENCRYPTION_KEY
        try:
            # Validate or normalize to 32 urlsafe base64 bytes
            self._fernet = Fernet(raw_key.encode("utf-8"))
        except Exception:
            # Fallback deterministic key for dev/test
            derived = base64.urlsafe_b64encode(raw_key.encode("utf-8").ljust(32)[:32])
            self._fernet = Fernet(derived)

    def encrypt_template(self, template: bytes) -> bytes:
        """Encrypt biometric template bytes before database insertion."""
        if not template:
            raise ValueError("Cannot encrypt empty template.")
        return self._fernet.encrypt(template)

    def decrypt_template(self, encrypted_template: bytes) -> bytes:
        """Decrypt biometric template bytes retrieved from database."""
        if not encrypted_template:
            raise ValueError("Cannot decrypt empty encrypted template.")
        return self._fernet.decrypt(encrypted_template)


biometric_cipher = BiometricEncryptionHelper()
