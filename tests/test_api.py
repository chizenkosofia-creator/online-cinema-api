import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.accounts.models import UserModel, ActivationToken


@pytest.mark.asyncio
async def test_read_root(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code in [200, 401, 404]


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient, db: AsyncSession):
    payload = {
        "email": "testcinema@example.com",
        "password": "StrongPassword123!"
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == payload["email"]
    assert data["is_active"] is False
    assert "id" in data

    result = await db.execute(select(UserModel).where(UserModel.email == payload["email"]))
    db_user = result.scalar_one_or_none()

    assert db_user is not None
    assert db_user.email == payload["email"]
    assert db_user.is_active is False

    token_result = await db.execute(
        select(ActivationToken).where(ActivationToken.user_id == db_user.id)
    )
    db_token = token_result.scalar_one_or_none()

    assert db_token is not None
    assert db_token.token is not None
    assert len(db_token.token) > 10
