import pytest


@pytest.mark.asyncio
async def test_create_order_unauthorized(async_client):
    response = await async_client.post(
        "/api/v1/orders/",
        json={"movie_ids": [1, 2]}
    )
    assert response.status_code == 401
