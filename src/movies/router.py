from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.movies.models import Genre, Movie
from src.movies.schemas import (
    GenreCreate,
    GenreResponse,
    MovieCreate,
    MovieResponse,
)

router = APIRouter(prefix="/movies", tags=["Movies & Genres"])

@router.post(
    "/genres/",
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_genre(
    genre_data: GenreCreate,
    session: AsyncSession = Depends(get_db),
):
    query = select(Genre).where(Genre.name == genre_data.name)
    existing_genre = (await session.execute(query)).scalar_one_or_none()
    if existing_genre:
        raise HTTPException(
            status_code=400, detail="Genre with this name already exists"
        )

    genre = Genre(name=genre_data.name)
    session.add(genre)
    await session.commit()
    await session.refresh(genre)
    return genre


@router.get("/genres/", response_model=List[GenreResponse])
async def list_genres(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Genre))
    return result.scalars().all()


@router.post(
    "/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie_data: MovieCreate,
    session: AsyncSession = Depends(get_db),
):
    genres = []
    if movie_data.genre_ids:
        genres_query = select(Genre).where(Genre.id.in_(movie_data.genre_ids))
        genres_result = await session.execute(genres_query)
        genres = list(genres_result.scalars().all())

    movie = Movie(
        title=movie_data.title,
        description=movie_data.description,
        release_year=movie_data.release_year,
        duration_minutes=movie_data.duration_minutes,
        rating=movie_data.rating,
        genres=genres,
    )
    session.add(movie)
    await session.commit()

    query = (
        select(Movie)
        .options(selectinload(Movie.genres))
        .where(Movie.id == movie.id)
    )
    res = await session.execute(query)
    return res.scalar_one()


@router.get("/", response_model=List[MovieResponse])
async def list_movies(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_db),
):
    query = (
        select(Movie)
        .options(selectinload(Movie.genres))
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: int, session: AsyncSession = Depends(get_db)
):
    query = (
        select(Movie)
        .options(selectinload(Movie.genres))
        .where(Movie.id == movie_id)
    )
    movie = (await session.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int, session: AsyncSession = Depends(get_db)
):
    query = select(Movie).where(Movie.id == movie_id)
    movie = (await session.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await session.delete(movie)
    await session.commit()
