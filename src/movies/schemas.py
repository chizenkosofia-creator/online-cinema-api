from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GenreBase(BaseModel):
    name: str = Field(..., max_length=100)


class GenreCreate(GenreBase):
    pass


class GenreResponse(GenreBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    release_year: int = Field(..., ge=1888, le=2100)
    duration_minutes: int = Field(..., gt=0)
    rating: float = Field(0.0, ge=0.0, le=10.0)


class MovieCreate(MovieBase):
    genre_ids: List[int] = []


class MovieResponse(MovieBase):
    id: int
    genres: List[GenreResponse] = []

    model_config = ConfigDict(from_attributes=True)
