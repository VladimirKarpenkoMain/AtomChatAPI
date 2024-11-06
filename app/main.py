from fastapi import FastAPI

from app.auth.router import router as AuthRouter
from app.chat.router import router as ChatRouter
from app.core.config import settings
from app.moderation.router import router as ModRouter

app = FastAPI(
    title="AtomChat API",
    docs_url=None if settings.MODE == "PROD" else "/docs",
    redoc_url=None if settings.MODE == "PROD" else "/redoc",
)

app.include_router(AuthRouter, prefix="/api/v1")
app.include_router(ChatRouter, prefix="/api/v1")
app.include_router(ModRouter, prefix="/api/v1")
