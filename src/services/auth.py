from datetime import datetime, timedelta, UTC
from typing import Optional, Literal

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from src.database.db import get_db
from src.conf.config import settings
from src.database.models import UserRole, User
from src.services.users import UserService

import pickle
import redis.asyncio as redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
redis_client = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=False
)


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)


def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
):
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    if expires_delta:
        access_token = create_token(data, expires_delta, "access")
    else:
        access_token = create_token(
            data, timedelta(minutes=settings.JWT_EXPIRATION_SECONDS), "access"
        )
    return access_token


async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    if expires_delta:
        refresh_token = create_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_token(
            data, timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRATION), "refresh"
        )
    return refresh_token


def create_password_reset_token(email: str, expires_hours: int = 1) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(hours=expires_hours)
    to_encode = {"sub": email, "exp": expire, "iat": now, "token_type": "reset"}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    cached_user = await redis_client.get(f"user:{username}")
    if cached_user:
        user = pickle.loads(cached_user)
        return user

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    await redis_client.setex(
        f"user:{username}", timedelta(minutes=10), pickle.dumps(user)
    )
    return user


async def verify_refresh_token(refresh_token: str, db: Session):
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")

        if username is None or token_type != "refresh":
            return None

        user_service = UserService(db)
        user = await user_service.get_user_by_refresh_token(username, refresh_token)
        return user
    except JWTError:
        return None


def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неправильний токен для перевірки електронної пошти",
        )


async def get_email_from_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        token_type = payload.get("token_type")
        if token_type != "reset":
            return None
        email = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    print(current_user.role)
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостатньо прав доступу")
    return current_user
