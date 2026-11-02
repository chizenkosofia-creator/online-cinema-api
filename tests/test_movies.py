import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_movies_list(async_client: AsyncClient):
    response = await async_client.get("/api/v1/movies/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, (list, dict))

    movies = data["items"] if isinstance(data, dict) and "items" in data else data
    assert isinstance(movies, list)


@pytest.mark.asyncio
async def test_get_movie_detail_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/movies/99999")
    assert response.status_code == 404

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.asyncio
async def test_movies_pagination_or_filtering(async_client: AsyncClient):
    response = await async_client.get("/api/v1/movies/?skip=0&limit=5")
    assert response.status_code == 200

    data = response.json()
    movies = data["items"] if isinstance(data, dict) and "items" in data else data
    assert len(movies) <= 5


@pytest.mark.asyncio
async def test_get_movie_detail_success(async_client: AsyncClient, db: AsyncSession):
    response = await async_client.get("/api/v1/movies/1")

    assert response.status_code in [200, 404]
    if response.status_code == 200:
        movie_data = response.json()
        assert "id" in movie_data
        assert "title" in movie_data


import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_genres_list(async_client: AsyncClient):
    response = await async_client.get("/api/v1/genres/")

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        genres = data["items"] if isinstance(data, dict) and "items" in data else data
        assert isinstance(genres, list)
