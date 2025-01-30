from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from src.database.models import UserRole


class ContactModel(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr = Field(min_length=7, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    birthday: date


class ContactResponse(ContactModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class RequestEmail(BaseModel):
    email: EmailStr
