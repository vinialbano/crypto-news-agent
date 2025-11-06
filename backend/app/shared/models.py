"""Shared models used across features."""
from sqlmodel import SQLModel


class Message(SQLModel):
    """Generic message response model."""

    message: str
