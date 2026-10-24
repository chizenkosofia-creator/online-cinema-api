from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.movies.models import (
    MovieModel,
    GenreModel,
    DirectorModel,
    StarModel,
)
from src.movies.schemas import (
    MovieCreate,
    MovieResponse,
    MoviePaginatedResponse,
    MovieUpdate,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie_data: MovieCreate,
        db: AsyncSession = Depends(get_db),
):
    genres = []
    if movie_data.genre_ids:
        res = await db.execute(select(GenreModel).where(GenreModel.id.in_(movie_data.genre_ids)))
        genres = list(res.scalars().all())

    directors = []
    if movie_data.director_ids:
        res = await db.execute(select(DirectorModel).where(DirectorModel.id.in_(movie_data.director_ids)))
        directors = list(res.scalars().all())

    stars = []
    if movie_data.star_ids:
        res = await db.execute(select(StarModel).where(StarModel.id.in_(movie_data.star_ids)))
        stars = list(res.scalars().all())

    movie = MovieModel(
        name=movie_data.name,
        year=movie_data.year,
        time=movie_data.time,
        imdb=movie_data.imdb,
        votes=movie_data.votes,
        meta_score=movie_data.meta_score,
        gross=movie_data.gross,
        description=movie_data.description,
        price=movie_data.price,
        certification_id=movie_data.certification_id,
        genres=genres,
        directors=directors,
        stars=stars,
    )

    db.add(movie)
    await db.commit()

    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
        .where(MovieModel.id == movie.id)
    )
    result = await db.execute(query)
    return result.scalar_one()


@router.get("/", response_model=MoviePaginatedResponse)
async def list_movies(
        page: int = Query(1, ge=1, description="Номер сторінки"),
        size: int = Query(10, ge=1, le=100, description="Кількість елементів на сторінці"),
        genre_id: Optional[int] = Query(None, description="Фільтрація за ID жанру"),
        year: Optional[int] = Query(None, description="Фільтрація за роком випуску"),
        search: Optional[str] = Query(None, description="Пошук за назвою або описом"),
        sort_by: Optional[str] = Query(
            "year",
            description="Сортування за полем: year, imdb, price, name",
        ),
        sort_order: Optional[str] = Query("desc", description="Порядок: asc або desc"),
        db: AsyncSession = Depends(get_db),
):
    query = select(MovieModel).options(
        selectinload(MovieModel.certification),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.directors),
        selectinload(MovieModel.stars),
    )

    if genre_id is not None:
        query = query.join(MovieModel.genres).where(GenreModel.id == genre_id)

    if year is not None:
        query = query.where(MovieModel.year == year)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                MovieModel.name.ilike(search_filter),
                MovieModel.description.ilike(search_filter),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    sort_columns = {
        "year": MovieModel.year,
        "imdb": MovieModel.imdb,
        "price": MovieModel.price,
        "name": MovieModel.name,
    }
    sort_col = sort_columns.get(sort_by, MovieModel.year)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdate,
        db: AsyncSession = Depends(get_db),
):
    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    update_data = movie_data.model_dump(exclude_unset=True)

    if "genre_ids" in update_data:
        genre_ids = update_data.pop("genre_ids")
        if genre_ids is not None:
            res = await db.execute(select(GenreModel).where(GenreModel.id.in_(genre_ids)))
            movie.genres = list(res.scalars().all())

    if "director_ids" in update_data:
        director_ids = update_data.pop("director_ids")
        if director_ids is not None:
            res = await db.execute(select(DirectorModel).where(DirectorModel.id.in_(director_ids)))
            movie.directors = list(res.scalars().all())

    if "star_ids" in update_data:
        star_ids = update_data.pop("star_ids")
        if star_ids is not None:
            res = await db.execute(select(StarModel).where(StarModel.id.in_(star_ids)))
            movie.stars = list(res.scalars().all())

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    """Delete a movie if it has not been purchased by any user (Moderator action)."""
    query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await db.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await db.delete(movie)
    await db.commit()
    return None
