from pydantic import BaseModel, field_validator, EmailStr
from enum import Enum
from app.validators.accounts import validate_email
from datetime import datetime
from typing import Optional

class UserGroupEnum(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_and_normalize_email(cls, value: str) -> str:
        """Field validator to ensure email is well-formed and normalized."""
        return validate_email(value)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str


class ResetPasswordRequestSchema(BaseModel):
    email: EmailStr

class ResetPasswordConfirmSchema(BaseModel):
    token: str
    new_password: str

class UserGroupResponseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserResponseSchema(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    group_id: int
    created_at: datetime
    updated_at: datetime
    group: Optional[UserGroupResponseSchema] = None

    class Config:
        from_attributes = True