from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "SecureVote API"
    APP_VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security & Cryptography
    SECRET_KEY: str = "securevote_super_secret_jwt_key_dev_2026_change_in_prod"
    # Fernet / AES key (32 bytes urlsafe base64)
    BIOMETRIC_ENCRYPTION_KEY: str = "s2l8yX0T_M0Vv5X2i3H_yYjX4Y8kQ7qZ8k1a2b3c4d4="
    ID_HASH_SALT: str = "securevote_salt_development_only_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    VOTE_TOKEN_EXPIRE_MINUTES: int = 2

    # Oracle Database Configuration (Thin Mode - No Oracle Client libraries required)
    ORACLE_USER: str = "securevote_app"
    ORACLE_PASSWORD: str = "change_me"
    ORACLE_HOST: str = "localhost"
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: str = "XEPDB1"
    DB_POOL_MIN: int = 2
    DB_POOL_MAX: int = 10
    DB_POOL_INCREMENT: int = 1

    # Fingerprint Provider Settings
    FINGERPRINT_PROVIDER: str = "mock"  # "mock", "dataset", "usb"
    FINGERPRINT_MATCH_THRESHOLD: float = 40.0
    DATASET_DIR: str = "backend/data/fingerprints"

    # Security Lockout & Rate Limiting
    MAX_FAILED_VERIFICATIONS: int = 3
    LOCKOUT_DURATION_MINUTES: int = 15
    RATE_LIMIT_PER_MINUTE: int = 120

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
