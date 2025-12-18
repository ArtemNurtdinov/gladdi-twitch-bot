import logging
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from config import config
from features.auth import auth_routes
from features.joke import joke_routes
from features.chat import chat_routes
from features.stream.data import stream_routes
from features.viewer import viewer_routes
from features.twitch.bot import bot_routes

logging.basicConfig(
    level=getattr(logging, config.logging.level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.logging.file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="GLaDDi Twitch Bot API",
    description="REST API для аналитики активности Twitch и Telegram бота",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(auth_routes.admin_router, prefix="/api/v1", tags=["Administration"])
app.include_router(chat_routes.router, prefix="/api/v1/messages", tags=["Chat"])
app.include_router(bot_routes.router, prefix="/api/v1", tags=["Twitch Bot"])
app.include_router(joke_routes.router, prefix="/api/v1", tags=["Jokes"])
app.include_router(stream_routes.router, prefix="/api/v1", tags=["Streams"])
app.include_router(viewer_routes.router, prefix="/api/v1", tags=["Viewers"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "GLaDDi Twitch Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "message": "API is running",
        "service": "GLaDDi Twitch Bot"
    }


if __name__ == "__main__":
    logger.info("Запуск API сервера...")
    uvicorn.run("main:app", host=config.dashboard.host, port=config.dashboard.port, log_level=config.dashboard.log_level)
