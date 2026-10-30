from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.movies.models import GenreModel, DirectorModel, StarModel, MovieModel
from src.movies.schemas import (
    GenreResponse,
    GenreCreate,
    PersonResponse,
    PersonCreate,
    GenreWithCountResponse,
    MovieResponse,
)

router = APIRouter(prefix="/movies/dictionaries", tags=["Movie Dictionaries"])


@router.get("/genres", response_model=List[GenreResponse])
async def get_genres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GenreModel).order_by(GenreModel.name))
    return result.scalars().all()


@router.post("/genres", response_model=GenreResponse, status_code=status.HTTP_201_CREATED)
async def create_genre(payload: GenreCreate, db: AsyncSession = Depends(get_db)):
    genre = GenreModel(name=payload.name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return genre


@router.get("/genres/with-counts", response_model=List[GenreWithCountResponse])
async def get_genres_with_movie_counts(db: AsyncSession = Depends(get_db)):
    """Returns a list of genres along with the count of movies in each genre."""
    query = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MovieModel.id).label("movies_count"),
        )
        .outerjoin(GenreModel.movies)
        .group_by(GenreModel.id)
        .order_by(GenreModel.name)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {"id": row.id, "name": row.name, "movies_count": row.movies_count}
        for row in rows
    ]


@router.get("/genres/{genre_id}/movies", response_model=List[MovieResponse])
async def get_movies_by_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve all movies belonging to a specific genre."""
    genre = (await db.execute(select(GenreModel).where(GenreModel.id == genre_id))).scalar_one_or_none()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
        .join(MovieModel.genres)
        .where(GenreModel.id == genre_id)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/directors", response_model=List[PersonResponse])
async def get_directors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DirectorModel).order_by(DirectorModel.name))
    return result.scalars().all()


@router.post("/directors", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_director(payload: PersonCreate, db: AsyncSession = Depends(get_db)):
    director = DirectorModel(name=payload.name)
    db.add(director)
    await db.commit()
    await db.refresh(director)
    return director


@router.get("/stars", response_model=List[PersonResponse])
async def get_stars(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StarModel).order_by(StarModel.name))
    return result.scalars().all()


@router.post("/stars", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_star(payload: PersonCreate, db: AsyncSession = Depends(get_db)):
    star = StarModel(name=payload.name)
    db.add(star)
    await db.commit()
    await db.refresh(star)
    return star
