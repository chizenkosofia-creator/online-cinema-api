from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependencies import get_current_user
from src.database import get_db
from src.movies.models import MovieModel, user_favorite_movies
from src.movies.schemas import MoviePaginatedResponse
from src.accounts.models import UserModel
router = APIRouter(prefix="/movies/favorites", tags=["Movie Favorites"])


@router.post("/{movie_id}", status_code=status.HTTP_201_CREATED)
async def add_movie_to_favorites(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a movie to the current user's favorites list."""
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(user_favorite_movies).where(
        and_(
            user_favorite_movies.c.user_id == current_user.id,
            user_favorite_movies.c.movie_id == movie_id,
        )
    )
    existing = (await db.execute(stmt)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Movie is already in favorites")

    insert_stmt = user_favorite_movies.insert().values(
        user_id=current_user.id,
        movie_id=movie_id,
    )
    await db.execute(insert_stmt)
    await db.commit()

    return {"detail": "Movie successfully added to favorites"}


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_movie_from_favorites(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a movie from the current user's favorites list."""
    delete_stmt = user_favorite_movies.delete().where(
        and_(
            user_favorite_movies.c.user_id == current_user.id,
            user_favorite_movies.c.movie_id == movie_id,
        )
    )
    result = await db.execute(delete_stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Movie not found in favorites")

    return None


@router.get("/", response_model=MoviePaginatedResponse)
async def list_user_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current user's favorite movies with pagination."""
    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
        .join(user_favorite_movies, user_favorite_movies.c.movie_id == MovieModel.id)
        .where(user_favorite_movies.c.user_id == current_user.id)
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    items = (await db.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }
