from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GenreResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PersonResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CertificationResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1888, le=2100)
    time: int = Field(..., gt=0)
    imdb: float = Field(..., ge=0.0, le=10.0)
    votes: int = Field(0, ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0.0)
    description: str
    price: Decimal = Field(..., ge=Decimal("0.00"))


class MovieCreate(MovieBase):
    certification_id: int
    genre_ids: List[int] = []
    director_ids: List[int] = []
    star_ids: List[int] = []


class MovieResponse(MovieBase):
    id: int
    uuid: str
    certification: CertificationResponse
    genres: List[GenreResponse] = []
    directors: List[PersonResponse] = []
    stars: List[PersonResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MoviePaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[MovieResponse]


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = Field(None, ge=1888, le=2100)
    time: Optional[int] = Field(None, gt=0)
    imdb: Optional[float] = Field(None, ge=0.0, le=10.0)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0.0)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None


class GenreCreate(BaseModel):
    name: str = Field(..., max_length=255)

class PersonCreate(BaseModel):
    name: str = Field(..., max_length=255)

class GenreWithCountResponse(BaseModel):
    id: int
    name: str
    movies_count: int

    model_config = ConfigDict(from_attributes=True)
