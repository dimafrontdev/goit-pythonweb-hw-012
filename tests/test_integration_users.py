from unittest.mock import AsyncMock, patch
import pytest
from conftest import test_user


@pytest.fixture
def mock_redis():
    """Mock Redis to prevent async errors in tests."""
    with patch(
        "src.services.auth.redis_client.get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None
        yield mock_get


def test_get_me(client, get_token, mock_redis):
    headers = {"Authorization": f"Bearer {get_token}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "avatar" in data


@patch("src.services.upload_file.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):
    fake_url = "<http://example.com/avatar.jpg>"
    mock_upload_file.return_value = fake_url

    headers = {"Authorization": f"Bearer {get_token}"}

    file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

    response = client.patch("/api/users/avatar", headers=headers, files=file_data)

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert data["avatar"] == fake_url

    mock_upload_file.assert_called_once()
