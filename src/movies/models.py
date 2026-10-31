from datetime import datetime
import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    String,
    Float,
    Text,
    DECIMAL,
    UniqueConstraint,
    Integer,
    ForeignKey,
    Table,
    Column,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.accounts.models import UserModel
from src.database import Base


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True),
)


user_favorite_movies = Table(
    "user_favorite_movies",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel", secondary=movie_genres, back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel", secondary=movie_stars, back_populates="stars"
    )

    def __repr__(self):
        return f"<Star(name='{self.name}')>"


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel", secondary=movie_directors, back_populates="directors"
    )

    def __repr__(self):
        return f"<Director(name='{self.name}')>"


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship("MovieModel", back_populates="certification")

    def __repr__(self):
        return f"<Certification(name='{self.name}')>"


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # тривалість у хвилинах
    imdb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=0.00)

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"), nullable=False
    )
    certification: Mapped["CertificationModel"] = relationship(
        "CertificationModel", back_populates="movies"
    )

    genres: Mapped[List["GenreModel"]] = relationship(
        "GenreModel", secondary=movie_genres, back_populates="movies"
    )
    directors: Mapped[List["DirectorModel"]] = relationship(
        "DirectorModel", secondary=movie_directors, back_populates="movies"
    )
    stars: Mapped[List["StarModel"]] = relationship(
        "StarModel", secondary=movie_stars, back_populates="movies"
    )
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    ratings_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    def __repr__(self):
        return f"<Movie(name='{self.name}', year={self.year}, imdb={self.imdb})>"


class MovieReactionModel(Base):
    __tablename__ = "movie_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    is_like: Mapped[bool] = mapped_column(Boolean)

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_reaction"),
    )


class MovieRatingModel(Base):
    __tablename__ = "movie_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )


class MovieCommentModel(Base):
    __tablename__ = "movie_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("movie_comments.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped["UserModel"] = relationship("UserModel", backref="comments")

    parent: Mapped[Optional["MovieCommentModel"]] = relationship(
        "MovieCommentModel", remote_side=[id], back_populates="replies", cascade="all, delete"
    )
    replies: Mapped[List["MovieCommentModel"]] = relationship(
        "MovieCommentModel", back_populates="parent", cascade="all, delete"
    )
    movie: Mapped["MovieModel"] = relationship("MovieModel", backref="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.user_id}, movie_id={self.movie_id})>"
