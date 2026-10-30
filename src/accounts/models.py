from datetime import datetime, timedelta, timezone
from enum import StrEnum, auto

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Relationship, validates

from src.security.password import get_password_hash, verify_password
from src.security.token import create_refresh_token
from src.validators.accounts import validate_email


class Base(DeclarativeBase):
    pass


class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class GenderEnum(StrEnum):
    MAN = auto()
    WOMAN = auto()


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(UserGroupEnum), unique=True, nullable=False)

    users = Relationship("User", back_populates="group")

    def __repr__(self):
        return f"<UserGroup(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    _hashed_password = Column("hashed_password", String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=False)

    group = Relationship("UserGroup", back_populates="users")
    profile = Relationship(
        "UserProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    activation_token = Relationship(
        "ActivationToken",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    password_reset_token = Relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    refresh_tokens = Relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders = Relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    cart = Relationship(
        "Cart",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"

    @property
    def password(self) -> None:
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, raw_password: str) -> None:
        verify_password(raw_password)
        self._hashed_password = get_password_hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, self._hashed_password)

    @validates("email")
    def validate_email_field(self, value):
        return validate_email(value)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar = Column(String(500), nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    info = Column(Text, nullable=True)

    user = Relationship("User", back_populates="profile")

    def __repr__(self):
        return (
            f"<UserProfile(id={self.id}, first_name={self.first_name}, "
            f"last_name={self.last_name}, gender={self.gender})>"
        )


class Token(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        default=create_refresh_token,
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )


class ActivationToken(Token):
    __tablename__ = "activation_tokens"

    user = Relationship("User", back_populates="activation_token")
    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<ActivationToken(id={self.id}, token={self.token}, expires_at={self.expires_at})>"


class PasswordResetToken(Token):
    __tablename__ = "password_reset_tokens"

    user = Relationship("User", back_populates="password_reset_token")
    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, token={self.token}, expires_at={self.expires_at})>"


class RefreshToken(Token):
    __tablename__ = "refresh_tokens"

    user = Relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, token={self.token}, expires_at={self.expires_at})>"
