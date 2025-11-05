"""Main API router."""
from fastapi import APIRouter

from app.core.config import settings

api_router = APIRouter()

# API routes will be added as they are implemented
# Examples:
# from app.api.routes import news, questions
# api_router.include_router(news.router)
# api_router.include_router(questions.router)
