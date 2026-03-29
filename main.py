import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.ai.gen.prompt.presentation import system_prompt_routes
from app.auth.presentation import auth_routes
from app.chat.presentation import chat_routes
from app.core.config.di.composition import load_config
from app.core.logger.di.composition import get_logger
from app.follow.presentation import followers_routes
from app.joke.presentation import joke_routes
from app.stream.presentation import stream_routes
from app.twitch.presentation import twitch_routes
from app.user.presentation import user_routes
from core.db import init_db

app = FastAPI(
    title="GLaDDi Bot API",
    description="API для управления GLaDDi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(auth_routes.admin_router, prefix="/api/v1/admin", tags=["Administration"])
app.include_router(system_prompt_routes.admin_router, prefix="/api/v1/ai", tags=["System Prompt"])
app.include_router(chat_routes.router, prefix="/api/v1/messages", tags=["Chat"])
app.include_router(twitch_routes.router, prefix="/api/v1/bot", tags=["Twitch Bot"])
app.include_router(joke_routes.router, prefix="/api/v1/jokes", tags=["Jokes"])
app.include_router(stream_routes.router, prefix="/api/v1/streams", tags=["Streams"])
app.include_router(followers_routes.router, prefix="/api/v1/followers", tags=["Followers"])
app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"])


@app.get("/", tags=["Health"])
async def root():
    return {"message": "GLaDDi Twitch Bot API", "version": "1.0.0", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "API is running", "service": "GLaDDi Twitch Bot"}


if __name__ == "__main__":
    config = load_config()
    host = config.application.host
    port = config.application.port

    init_db(config.db)

    logger = get_logger()

    logger.log_info(f"Запуск на http://{host}:{port}")

    uvicorn.run("main:app", host=host, port=port, log_level="info")
