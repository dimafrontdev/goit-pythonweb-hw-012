from typing import Optional
from datetime import datetime
from enum import Enum

from sqlalchemy import Integer, String, func, ForeignKey, Boolean, Enum as SqlEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped, DeclarativeBase
from sqlalchemy.sql.sqltypes import DateTime


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String, unique=True)
    email = mapped_column(String, unique=True)
    hashed_password = mapped_column(String)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at = mapped_column(DateTime, default=func.now())
    avatar = mapped_column(String(255), nullable=True)
    confirmed = mapped_column(Boolean, default=False)
    role = mapped_column(SqlEnum(UserRole), default=UserRole.USER, nullable=False)


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    birthday: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    user_id = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    user = relationship("User", backref="notes")
