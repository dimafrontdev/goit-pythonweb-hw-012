from pydantic import ConfigDict, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_TOKEN_EXPIRATION: int = 60 * 24 * 7  # 7 days

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 465
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int = 326488457974591
    CLOUDINARY_API_SECRET: str = "secret"

    REDIS_PORT: int = 6379
    REDIS_HOST: str = "localhost"

    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()
