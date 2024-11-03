from fastapi import FastAPI
from app.auth.router import router as AuthRouter
from app.chat.router import router as ChatRouter
from app.moderation.router import router as ModRouter
from app.core.config import settings

app = FastAPI(
    title="AtomChat API",
    docs_url=None if settings.DEBUG == False else '/docs',
    redoc_url=None if settings.DEBUG == False else '/redoc',
)

app.include_router(ChatRouter)
app.include_router(AuthRouter)
app.include_router(ModRouter)


