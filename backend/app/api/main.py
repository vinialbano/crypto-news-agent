"""Main API router - registers all feature routers."""

from fastapi import APIRouter

from app.features.news.router import router as news_router
from app.features.questions.router import router as questions_router

api_router = APIRouter()

# Register feature routers
api_router.include_router(news_router, prefix="/news", tags=["news"])
api_router.include_router(questions_router, prefix="/questions", tags=["questions"])
