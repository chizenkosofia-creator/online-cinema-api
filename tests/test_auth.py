from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.accounts.models import UserModel, ActivationToken


import pytest


@pytest.mark.asyncio
async def test_user_registration(async_client):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "group_id": 1
        }
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "email" in data or "id" in data


@pytest.mark.asyncio
async def test_user_login(async_client):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "StrongPassword123!",
            "group_id": 1
        }
    )
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": "loginuser@example.com",
            "password": "StrongPassword123!"
        }
    )
    assert response.status_code == 403


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
    assert len(db_token.token) > 20


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, db: AsyncSession):
    payload = {
        "email": "loginuser@example.com",
        "password": "StrongPassword123!"
    }
    await async_client.post("/api/v1/auth/register", json=payload)

    result = await db.execute(select(UserModel).where(UserModel.email == payload["email"]))
    db_user = result.scalar_one_or_none()
    db_user.is_active = True
    await db.commit()

    login_data = {
        "username": payload["email"],
        "password": payload["password"]
    }

    response = await async_client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data.get("token_type") == "bearer"

