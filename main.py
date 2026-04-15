import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.ai.gen.prompt.presentation import system_prompt_routes
from app.auth.di.container import AuthContainer
from app.auth.presentation import auth_routes
from app.bot.bot_manager import BotManager
from app.bot.presentation.api import bot_routes, bot_twitch_routes
from app.chat.presentation import chat_routes
from app.core.di.application_container import ApplicationContainer
from app.follow.presentation import followers_routes
from app.joke.di.container import JokeContainer
from app.joke.presentation.api import joke_routes
from app.shop.presentation.api import shop_routes
from app.stream.presentation import stream_routes
from app.viewer.presentation.api import viewer_routes
from core.db import init_db


class Application:
    _APPLICATION_NAME = "GLaDDi Bot"
    _APPLICATION_DESCRIPTION = "API для управления GLaDDi"
    _VERSION = "1.0.0"
    _DOCS_URL = "/docs"

    def __init__(self, container: ApplicationContainer):
        self.container = container
        self.fast_api = FastAPI(
            title=self._APPLICATION_NAME,
            description=self._APPLICATION_DESCRIPTION,
            version=self._VERSION,
            docs_url=self._DOCS_URL,
        )

        self._setup_middleware()
        self._setup_routes()
        self._setup_health_checks()
        self._setup_state()

    def _setup_middleware(self):
        self.fast_api.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_state(self):
        self.fast_api.state.logger = self.container.logger
        self.fast_api.state.config = self.container.config
        self.fast_api.state.auth_container = AuthContainer(self.container.config.application)
        self.fast_api.state.joke_container = JokeContainer(self.container.logger)
        self.fast_api.state.bot_manager = BotManager(
            config=self.container.config.bot,
            telegram_config=self.container.config.telegram,
            llmbox_config=self.container.config.llmbox,
            intent_detector_config=self.container.config.intent_detector,
            logger=self.container.logger,
        )

    def _setup_routes(self):
        self.fast_api.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
        self.fast_api.include_router(auth_routes.admin_router, prefix="/api/v1/admin", tags=["Administration"])
        self.fast_api.include_router(system_prompt_routes.admin_router, prefix="/api/v1/ai", tags=["System Prompt"])
        self.fast_api.include_router(chat_routes.router, prefix="/api/v1/messages", tags=["Chat"])
        self.fast_api.include_router(bot_routes.router, prefix="/api/v1/bot", tags=["Bot Manager"])
        self.fast_api.include_router(bot_twitch_routes.router, prefix="/api/v1/bot", tags=["Twitch Bot"])
        self.fast_api.include_router(joke_routes.router, prefix="/api/v1/jokes", tags=["Jokes"])
        self.fast_api.include_router(stream_routes.router, prefix="/api/v1/streams", tags=["Streams"])
        self.fast_api.include_router(followers_routes.router, prefix="/api/v1/followers", tags=["Followers"])
        self.fast_api.include_router(viewer_routes.router, prefix="/api/v1", tags=["Users"])
        self.fast_api.include_router(shop_routes.router, prefix="/api/v1/shop", tags=["Shop"])

    def _setup_health_checks(self):
        @self.fast_api.get("/", tags=["Health"])
        async def root():
            return {"message": "GLaDDi Twitch Bot API", "version": "1.0.0", "docs": "/docs"}

        @self.fast_api.get("/health", tags=["Health"])
        async def health_check():
            return {"status": "healthy", "message": "API is running", "service": "GLaDDi Twitch Bot"}

    def run(self):
        config = self.container.config
        logger = self.container.logger

        host = config.application.host
        port = config.application.port

        init_db(config.db)

        logger.log_info(f"Запуск на http://{host}:{port}")

        uvicorn.run(app=self.fast_api, host=host, port=port, log_level="info")


if __name__ == "__main__":
    app_container = ApplicationContainer()
    Application(app_container).run()
