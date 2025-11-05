import hashlib
import uuid
from datetime import datetime

from pydantic import EmailStr
from pgvector.sqlalchemy import Vector
from sqlmodel import Column, Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# News Source Model
class NewsSource(SQLModel, table=True):
    __tablename__ = "news_sources"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    rss_url: str = Field(max_length=2048, unique=True)
    is_active: bool = Field(default=True, index=True)
    last_ingestion_at: datetime | None = None
    last_error: str | None = Field(default=None, max_length=1000)
    ingestion_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# News Article Model
class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"

    id: int | None = Field(default=None, primary_key=True)
    content_hash: str = Field(max_length=64, unique=True, index=True)
    title: str = Field(max_length=500)
    url: str = Field(max_length=2048)
    content: str
    source_name: str = Field(max_length=100, index=True)
    published_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    embedding: list[float] = Field(sa_column=Column(Vector(768)))

    @classmethod
    def compute_content_hash(cls, title: str, url: str) -> str:
        """Compute SHA-256 hash of title + URL for duplicate detection"""
        content = f"{title}|{url}"
        return hashlib.sha256(content.encode()).hexdigest()


# Public schemas for API responses
class NewsSourcePublic(SQLModel):
    id: int
    name: str
    rss_url: str
    is_active: bool
    last_ingestion_at: datetime | None
    last_error: str | None
    ingestion_count: int
    created_at: datetime


class NewsArticlePublic(SQLModel):
    id: int
    title: str
    url: str
    source_name: str
    published_at: datetime | None
    ingested_at: datetime
    # Note: embedding not exposed in public API


# Chat History Models for Q&A persistence
class Question(SQLModel, table=True):
    __tablename__ = "questions"

    id: int | None = Field(default=None, primary_key=True)
    text: str = Field(max_length=1000)
    submitted_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationship to answers
    answers: list["Answer"] = Relationship(back_populates="question")


class Answer(SQLModel, table=True):
    __tablename__ = "answers"

    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="questions.id", nullable=False, index=True)
    full_text: str
    status: str = Field(max_length=20)  # 'streaming' | 'complete' | 'error'
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: datetime | None = None

    # Relationships
    question: Question | None = Relationship(back_populates="answers")
    source_articles: list["AnswerSourceArticle"] = Relationship(back_populates="answer")


class AnswerSourceArticle(SQLModel, table=True):
    __tablename__ = "answer_source_articles"

    id: int | None = Field(default=None, primary_key=True)
    answer_id: int = Field(foreign_key="answers.id", nullable=False, index=True)
    article_id: int = Field(foreign_key="news_articles.id", nullable=False, index=True)
    relevance_score: float | None = None

    # Relationships
    answer: Answer | None = Relationship(back_populates="source_articles")
