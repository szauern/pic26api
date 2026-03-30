from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.redis_client import init_redis, close_redis
from app.routers import translations, webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - globális kapcsolatok inicializálása
    await init_redis()
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Translation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translations.router)
app.include_router(webhook.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}
