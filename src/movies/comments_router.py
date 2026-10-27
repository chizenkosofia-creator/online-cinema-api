from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.movies.models import MovieModel, MovieCommentModel
from src.movies.schemas import CommentCreate, CommentUpdate, CommentResponse
from src.accounts.models import User
from src.dependencies import get_current_user

router = APIRouter(prefix="/movies", tags=["Movie Comments"])


@router.post("/{movie_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    movie_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if payload.parent_id:
        parent_comment = (
            await db.execute(
                select(MovieCommentModel).where(
                    MovieCommentModel.id == payload.parent_id,
                    MovieCommentModel.movie_id == movie_id,
                )
            )
        ).scalar_one_or_none()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found for this movie")

    comment = MovieCommentModel(
        user_id=current_user.id,
        movie_id=movie_id,
        parent_id=payload.parent_id,
        content=payload.content,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/{movie_id}/comments", response_model=List[CommentResponse])
async def get_movie_comments(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == movie_id))).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    query = (
        select(MovieCommentModel)
        .where(MovieCommentModel.movie_id == movie_id, MovieCommentModel.parent_id.is_(None))
        .options(selectinload(MovieCommentModel.replies))
        .order_by(MovieCommentModel.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (
        await db.execute(select(MovieCommentModel).where(MovieCommentModel.id == comment_id))
    ).scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this comment")

    comment.content = payload.content
    await db.commit()
    await db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (
        await db.execute(select(MovieCommentModel).where(MovieCommentModel.id == comment_id))
    ).scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    await db.delete(comment)
    await db.commit()
    return None
