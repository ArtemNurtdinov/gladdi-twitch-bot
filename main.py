import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.ai.gen.di.container import AIContainer
from app.ai.gen.llm.presentation import llm_routes
from app.ai.gen.prompt.presentation import system_prompt_routes
from app.auth.di.container import AuthContainer
from app.auth.presentation import auth_routes
from app.battle.di.container import BattleContainer
from app.betting.di.container import BettingContainer
from app.bot.bot_manager import BotManager
from app.bot.presentation.api import bot_routes, bot_twitch_routes
from app.chat.di.container import ChatContainer
from app.chat.presentation import chat_routes
from app.core.di.application_container import ApplicationContainer
from app.economy.di.container import EconomyContainer
from app.equipment.di.container import EquipmentContainer
from app.follow.di.container import FollowContainer
from app.follow.presentation import followers_routes
from app.joke.di.container import JokeContainer
from app.joke.presentation.api import joke_routes
from app.minigame.di.container import MinigameContainer
from app.moderation.application.moderation_service import ModerationService
from app.notification.di.container import NotificationContainer
from app.platform.command.ask.di.container import AskContainer
from app.platform.di.container import PlatformContainer
from app.shop.di.container import ShopContainer
from app.shop.presentation.api import shop_routes
from app.stream.di.container import StreamContainer
from app.stream.presentation import stream_routes
from app.viewer.di.container import ViewerContainer
from app.viewer.infrastructure.cache.viewer_cache_service import ViewerCacheService
from app.viewer.presentation.api import viewer_routes
from core.db import db_ro_session, db_rw_session, init_db


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
        self.fast_api.state.joke_container = JokeContainer(
            session_factory_ro=db_ro_session, session_factory_rw=db_rw_session, logger=self.container.logger
        )
        ai_container = AIContainer(
            session_factory_ro=db_ro_session,
            session_factory_rw=db_rw_session,
            llmbox_host=self.container.config.llmbox.host,
            intent_detector_host=self.container.config.intent_detector.host,
        )
        shop_container = ShopContainer()
        stream_container = StreamContainer()
        chat_container = ChatContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session, logger=self.container.logger)
        economy_container = EconomyContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
        follow_container = FollowContainer()
        betting_container = BettingContainer()
        ask_container = AskContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)

        self.fast_api.state.ai_container = ai_container
        self.fast_api.state.stream_container = stream_container
        self.fast_api.state.economy_container = economy_container
        self.fast_api.state.follow_container = follow_container
        equipment_container = EquipmentContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)

        minigame_container = MinigameContainer(
            session_factory_ro=db_ro_session, session_factory_rw=db_rw_session, logger=self.container.logger
        )
        notification_container = NotificationContainer(self.container.config.telegram.bot_token)
        battle_container = BattleContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
        viewer_container = ViewerContainer()

        platform_container = PlatformContainer(
            client_id=self.container.config.twitch.client_id,
            client_secret=self.container.config.twitch.client_secret,
            session_factory_ro=db_ro_session,
            session_factory_rw=db_rw_session,
            logger=self.container.logger,
        )
        platform_repository = platform_container.platform_repository()

        viewer_cache = ViewerCacheService(platform_repository)

        moderation_service = ModerationService(
            platform_repository=platform_repository,
            user_cache=viewer_cache,
            logger=self.container.logger,
        )

        self.fast_api.state.viewer_container = viewer_container

        self.fast_api.state.bot_manager = BotManager(
            config=self.container.config.bot,
            telegram_config=self.container.config.telegram,
            llmbox_config=self.container.config.llmbox,
            intent_detector_config=self.container.config.intent_detector,
            logger=self.container.logger,
            shop_item_repository_factory=shop_container.shop_item_repository_factory,
            minigame_repository=minigame_container.minigame_repository(),
            get_used_word_use_case=minigame_container.get_used_words_use_case(),
            add_used_word_use_case=minigame_container.add_used_word_use_case(),
            stream_repository_factory=stream_container.stream_repository_factory,
            economy_policy_factory=economy_container.economy_policy_factory,
            handle_balance_use_case=economy_container.handle_balance_use_case(chat_container.chat_use_case()),
            chat_repository_factory=chat_container.chat_repository_factory,
            chat_use_case=chat_container.chat_use_case(),
            followers_repository_factory=follow_container.followers_repository_factory,
            betting_service_factory=betting_container.betting_service_factory,
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
            calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
            roll_cooldown_use_case=equipment_container.roll_cooldown_use_case(),
            add_equipment_use_case=equipment_container.add_equipment_use_case(),
            equipment_exists_use_case=equipment_container.equipment_exists_use_case(),
            notification_repository=notification_container.notification_repository(),
            battle_uow_factory=battle_container.battle_uow_factory(
                economy_policy_factory=economy_container.economy_policy_factory,
                chat_use_case=chat_container.chat_use_case(),
                conversation_service_factory=ai_container.conversation_service_factory,
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
            ),
            battle_use_case=battle_container.battle_use_case(),
            ask_uow_factory=ask_container.ask_uow_factory(
                chat_repository_factory=chat_container.chat_repository_factory,
                conversation_service_factory=ai_container.conversation_service_factory,
                system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
            ),
            platform_container=platform_container,
            viewer_repository_factory=viewer_container.viewer_repository_factory,
            chat_message_uow_factory=chat_container.chat_message_uow_factory(
                economy_policy_factory=economy_container.economy_policy_factory,
                stream_repository_factory=stream_container.stream_repository_factory,
                viewer_repository_factory=viewer_container.viewer_repository_factory,
                conversation_service_factory=ai_container.conversation_service_factory,
                system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
            ),
            chat_summarizer_job=chat_container.chat_summarizer_job(
                stream_repository_factory=stream_container.stream_repository_factory,
                generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
            ),
            viewer_cache=viewer_cache,
            moderation_service=moderation_service,
            followage_command_handler=platform_container.followage_command_handler(
                command_prefix=self.container.config.bot.prefix,
                command_name=self.container.config.bot.command_followage,
                generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
                chat_repository_factory=chat_container.chat_repository_factory,
                conversation_service_factory=ai_container.conversation_service_factory,
                system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
                platform_repository=platform_repository,
            ),
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
        self.fast_api.include_router(llm_routes.router, prefix="/api/v1/assistant", tags=["Assistant"])

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
