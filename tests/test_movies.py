import pytest


@pytest.mark.asyncio
async def test_get_movies_list(async_client):
    response = await async_client.get("/api/v1/movies/")
    assert response.status_code == 200
    assert isinstance(response.json(), (list, dict))


@pytest.mark.asyncio
async def test_get_movie_detail_not_found(async_client):
    response = await async_client.get("/api/v1/movies/99999")
    assert response.status_code == 404
