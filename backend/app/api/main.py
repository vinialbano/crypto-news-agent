"""Main API router - registers all feature routers."""

from fastapi import APIRouter

from app.api.routes.news import router as news_router
from app.api.routes.questions import router as questions_router

api_router = APIRouter()

# Register feature routers
api_router.include_router(news_router, prefix="/news", tags=["news"])
api_router.include_router(questions_router, prefix="/questions", tags=["questions"])
