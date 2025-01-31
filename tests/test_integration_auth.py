from unittest.mock import Mock
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select
from src.database.models import User
from tests.conftest import TestingSessionLocal

user_data = {
    "username": "userTest",
    "email": "userTest@gmail.com",
    "password": "12345678",
    "role": "user",
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Користувач з таким email вже існує"


def test_not_confirmed_login(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Електронна адреса не підтверджена"


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    async with TestingSessionLocal() as session:
        current_user.refresh_token = data["refresh_token"]
        await session.commit()

    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("username"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Неправильний логін або пароль"


def test_wrong_username_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": "username", "password": user_data.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Неправильний логін або пароль"


def test_validation_error_login(client):
    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_refresh_token(client):
    response = client.post(
        "/api/auth/refresh-token", json={"refresh_token": "invalidtoken"}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_confirm_email(client, get_token, monkeypatch):
    mock_email_service = AsyncMock(return_value=user_data["email"])
    monkeypatch.setattr("src.api.auth.get_email_from_token", mock_email_service)

    response = client.get(f"/api/auth/confirmed_email/{get_token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Електронну пошту підтверджено"


def test_request_email_for_non_existent_user(client):
    response = client.post(
        "/api/auth/request_email", json={"email": "notfound@example.com"}
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Такого користувача не існує"


def test_request_password_reset(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_password_reset_email", mock_send_email)

    response = client.post(
        "/api/auth/request_password_reset", json={"email": user_data["email"]}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Посилання для скидання пароля відправлено на ваш email."


def test_invalid_token_password_reset(client):
    response = client.post(
        "/api/auth/confirm_password_reset",
        json={"token": "invalidtoken", "new_password": "new_secure_password"},
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Невірний або прострочений токен"
