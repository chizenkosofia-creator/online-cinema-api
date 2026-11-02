import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.accounts.models import UserModel, ActivationToken



@pytest.mark.asyncio
async def test_read_root(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 404


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


@pytest.mark.asyncio
async def test_user_registration_is_inactive(async_client: AsyncClient, db: AsyncSession):
    payload = {
        "email": "test_register@example.com",
        "password": "SecurePassword123"
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == payload["email"]
    assert data["is_active"] is False

    result = await db.execute(
        select(UserModel).where(UserModel.email == payload["email"])
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_active is False

    token_result = await db.execute(
        select(ActivationToken).where(ActivationToken.user_id == user.id)
    )
    activation_token = token_result.scalar_one_or_none()

    assert activation_token is not None
    assert not activation_token.token.startswith("eyJ")
    assert len(activation_token.token) >= 32


@pytest.mark.asyncio
async def test_login_blocked_for_inactive_user(async_client: AsyncClient):
    payload = {
        "email": "test_register_unique@example.com",
        "password": "SecurePassword123"
    }

    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Account is not activated."


@pytest.mark.asyncio
async def test_account_activation_flow(async_client: AsyncClient, db: AsyncSession):
    email = "activate_flow@example.com"
    password = "SecurePassword123"

    reg_response = await async_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password
    })
    assert reg_response.status_code == 201

    result = await db.execute(
        select(UserModel).where(UserModel.email == email)
    )
    user = result.scalar_one_or_none()

    token_result = await db.execute(
        select(ActivationToken).where(ActivationToken.user_id == user.id)
    )
    activation_token = token_result.scalar_one_or_none()

    activate_response = await async_client.post(f"/api/v1/auth/activate?token={activation_token.token}")
    assert activate_response.status_code == 200

    await db.refresh(user)
    assert user.is_active is True

    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_resend_activation_token(async_client: AsyncClient, db: AsyncSession):
    email = "resend_test@example.com"
    password = "StrongPassword123!"

    await async_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password
    })

    response = await async_client.post("/api/v1/auth/resend-activation", json={
        "email": email
    })

    assert response.status_code == 200
    assert "sent" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(async_client: AsyncClient, db: AsyncSession):
    email = "reset_pass_test@example.com"
    password = "OriginalPassword123!"
    new_password = "BrandNewPassword456!"

    await async_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password
    })

    forgot_response = await async_client.post("/api/v1/auth/forgot-password", json={
        "email": email
    })
    assert forgot_response.status_code == 200

    from src.accounts.models import UserModel, PasswordResetToken

    user_result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = user_result.scalar_one_or_none()

    token_result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    reset_token = token_result.scalar_one_or_none()

    assert reset_token is not None
    assert reset_token.token is not None

    reset_response = await async_client.post("/api/v1/auth/reset-password", json={
        "token": reset_token.token,
        "new_password": new_password
    })

    assert reset_response.status_code == 200
    assert "successfully reset" in reset_response.json()["message"].lower()

    user.is_active = True
    db.add(user)
    await db.commit()

    login_response = await async_client.post("/api/v1/auth/login", data={
        "username": email,
        "password": new_password
    })

    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
