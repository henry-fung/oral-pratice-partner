from fastapi import APIRouter

api_router = APIRouter()

# 包含所有路由
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.scenarios import router as scenarios_router
from backend.api.sentences import router as sentences_router
from backend.api.vocabulary import router as vocabulary_router

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(scenarios_router)
api_router.include_router(sentences_router)
api_router.include_router(vocabulary_router)

__all__ = ["api_router"]
