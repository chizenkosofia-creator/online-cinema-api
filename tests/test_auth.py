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
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
