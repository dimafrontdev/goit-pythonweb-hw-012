import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
def test_healthchecker(client, monkeypatch):
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = 1
    monkeypatch.setattr("src.api.utils.get_db", lambda: mock_db)

    response = client.get("/api/healthchecker")

    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Welcome to FastAPI!"}
