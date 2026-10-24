from typing import List, Optional
from sqlalchemy import String, Text, Integer, Float, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    movies: Mapped[List["Movie"]] = relationship(
        "Movie", secondary=movie_genres, back_populates="genres"
    )


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    release_year: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    genres: Mapped[List[Genre]] = relationship(
        "Genre", secondary=movie_genres, back_populates="movies", lazy="selectin"
    )
