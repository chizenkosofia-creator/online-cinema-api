from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.movies.models import MovieModel, MovieReactionModel, MovieRatingModel
from src.movies.schemas import MovieReactionCreate, MovieRatingCreate, MovieInteractionResponse
from src.accounts.models import UserModel
from src.dependencies import get_current_user

router = APIRouter(prefix="/movies", tags=["Movie Interactions"])


@router.post("/{movie_id}/reaction", response_model=MovieInteractionResponse)
async def react_to_movie(
    movie_id: int,
    payload: MovieReactionCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(MovieReactionModel).where(
        and_(MovieReactionModel.user_id == current_user.id, MovieReactionModel.movie_id == movie_id)
    )
    existing_reaction = (await db.execute(stmt)).scalar_one_or_none()

    if existing_reaction:
        if existing_reaction.is_like == payload.is_like:
            await db.delete(existing_reaction)
            await db.commit()
            return {"detail": "Reaction removed"}
        else:
            existing_reaction.is_like = payload.is_like
            await db.commit()
            return {"detail": "Reaction updated"}
    else:
        reaction = MovieReactionModel(
            user_id=current_user.id,
            movie_id=movie_id,
            is_like=payload.is_like,
        )
        db.add(reaction)
        await db.commit()
        return {"detail": "Reaction added"}


@router.post("/{movie_id}/rating", response_model=MovieInteractionResponse)
async def rate_movie(
    movie_id: int,
    payload: MovieRatingCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(MovieRatingModel).where(
        and_(MovieRatingModel.user_id == current_user.id, MovieRatingModel.movie_id == movie_id)
    )
    existing_rating = (await db.execute(stmt)).scalar_one_or_none()

    if existing_rating:
        existing_rating.score = payload.score
    else:
        new_rating = MovieRatingModel(
            user_id=current_user.id,
            movie_id=movie_id,
            score=payload.score,
        )
        db.add(new_rating)

    await db.commit()

    ratings_query = select(func.avg(MovieRatingModel.score), func.count(MovieRatingModel.id)).where(
        MovieRatingModel.movie_id == movie_id
    )
    res = (await db.execute(ratings_query)).first()
    avg_score, total_count = res[0], res[1]

    movie.average_rating = round(float(avg_score), 2) if avg_score else 0.0
    movie.ratings_count = total_count or 0
    await db.commit()

    return {
        "detail": "Rating successfully submitted",
        "average_rating": movie.average_rating,
        "ratings_count": movie.ratings_count,
    }
