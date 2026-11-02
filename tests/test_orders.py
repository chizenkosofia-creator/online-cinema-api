import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.accounts.models import UserModel
from src.movies.models import MovieModel


@pytest.mark.asyncio
async def test_create_order_unauthorized(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/orders/",
        json={"movie_ids": [1, 2]}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_orders_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/orders/my")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_order_success(async_client: AsyncClient, db: AsyncSession):
    payload = {
        "email": "orderuser@example.com",
        "password": "StrongPassword123!",
        "group_id": 1
    }
    await async_client.post("/api/v1/auth/register", json=payload)

    result = await db.execute(select(UserModel).where(UserModel.email == payload["email"]))
    db_user = result.scalar_one_or_none()
    db_user.is_active = True
    await db.commit()

    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]}
    )
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    movie = MovieModel(id=101, name="Interstellar", year=2014, price=150.00, time=169, description="good movie", certification_id=2)
    db.add(movie)
    await db.commit()

    order_payload = {
        "movie_ids": [101]
    }
    response = await async_client.post("/api/v1/orders/", json=order_payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert "order" in data
    assert data["order"]["status"] == "pending"


@pytest.mark.asyncio
async def test_get_user_orders_success(async_client: AsyncClient, db: AsyncSession):
    payload = {
        "email": "historyuser@example.com",
        "password": "StrongPassword123!",
        "group_id": 1
    }
    await async_client.post("/api/v1/auth/register", json=payload)

    result = await db.execute(select(UserModel).where(UserModel.email == payload["email"]))
    db_user = result.scalar_one_or_none()
    db_user.is_active = True
    await db.commit()

    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]}
    )
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/orders/my", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
