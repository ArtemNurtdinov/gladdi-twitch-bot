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
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.di.container import ChatContainer
from app.chat.presentation import chat_routes
from app.core.di.application_container import ApplicationContainer
from app.economy.di.container import EconomyContainer
from app.equipment.di.container import EquipmentContainer
from app.follow.di.container import FollowContainer
from app.follow.presentation import followers_routes
from app.joke.di.container import JokeContainer
from app.joke.presentation.api import joke_routes
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.minigame.di.container import MinigameContainer
from app.moderation.application.moderation_service import ModerationService
from app.notification.di.container import NotificationContainer
from app.platform.chat.application.usecase.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.usecase.handle_reply_use_case import HandleReplyUseCase
from app.platform.chat.infrastructure.twitch_platform_client import TwitchPlatformChatClient
from app.platform.command.application.command_router import CommandRouterImpl
from app.platform.command.ask.application.ask_command_handler import AskCommandHandler
from app.platform.command.ask.application.handle_ask_use_case import HandleAskUseCase
from app.platform.command.ask.di.container import AskContainer
from app.platform.command.balance.application.balance_command_handler import BalanceCommandHandler
from app.platform.command.battle.application.battle_command_handler import BattleCommandHandler
from app.platform.command.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.platform.command.domain.command_router import CommandRouter
from app.platform.di.container import PlatformContainer
from app.shop.di.container import ShopContainer
from app.shop.presentation.api import shop_routes
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.di.container import StreamContainer
from app.stream.presentation import stream_routes
from app.task.domain.model.task import Task
from app.task.infrastructure.runner import BackgroundTaskRunner
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
        joke_container = JokeContainer(session_factory_ro=db_ro_session, session_factory_rw=db_rw_session, logger=self.container.logger)
        self.fast_api.state.joke_container = joke_container
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
        chat_summary_state = ChatSummaryState()

        self.fast_api.state.viewer_container = viewer_container
        self.fast_api.state.platform_container = platform_container

        minigame_repository = minigame_container.minigame_repository()

        chat_message_uow_factory = chat_container.chat_message_uow_factory(
            economy_policy_factory=economy_container.economy_policy_factory,
            stream_repository_factory=stream_container.stream_repository_factory,
            viewer_repository_factory=viewer_container.viewer_repository_factory,
            conversation_service_factory=ai_container.conversation_service_factory,
            system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
        )

        followage_command_handler = platform_container.followage_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_followage,
            generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
            chat_repository_factory=chat_container.chat_repository_factory,
            conversation_service_factory=ai_container.conversation_service_factory,
            system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
            platform_repository=platform_repository,
        )

        ask_command_handler = AskCommandHandler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_gladdi,
            handle_ask_use_case=HandleAskUseCase(
                get_intent_from_text_use_case_factory=ai_container.get_intent_from_text_use_case_factory,
                prompt_service=ai_container.prompt_service,
                ask_uow_factory=ask_container.ask_uow_factory(
                    chat_repository_factory=chat_container.chat_repository_factory,
                    conversation_service_factory=ai_container.conversation_service_factory,
                    system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
                ),
                generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
                session_factory_ro=db_ro_session,
            ),
        )

        battle_command_handler = BattleCommandHandler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_fight,
            handle_battle_use_case=HandleBattleUseCase(
                battle_uow=battle_container.battle_uow_factory(
                    economy_policy_factory=economy_container.economy_policy_factory,
                    chat_use_case=chat_container.chat_use_case(),
                    conversation_service_factory=ai_container.conversation_service_factory,
                    get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                ),
                generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
                calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
                db_ro_session=db_ro_session,
            ),
            chat_moderation=moderation_service,
            battle_waiting_user={"value": None},
        )

        roll_command_handler = platform_container.roll_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_roll,
            economy_policy_factory=economy_container.economy_policy_factory,
            betting_service_factory=betting_container.betting_service_factory,
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
            chat_use_case=chat_container.chat_use_case(),
            roll_cooldown_use_case=equipment_container.roll_cooldown_use_case(),
            calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
            chat_moderation_port=moderation_service,
        )

        balance_command_handler = BalanceCommandHandler(
            handle_balance_use_case=economy_container.handle_balance_use_case(chat_container.chat_use_case())
        )

        bonus_command_handler = platform_container.bonus_command_handler(
            stream_repository_factory=stream_container.stream_repository_factory,
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
        )

        transfer_command_handler = platform_container.transfer_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_transfer,
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
        )

        shop_command_handler = platform_container.shop_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_shop_name=self.container.config.bot.command_shop,
            command_buy_name=self.container.config.bot.command_buy,
            economy_policy_factory=economy_container.economy_policy_factory,
            add_equipment_use_case=equipment_container.add_equipment_use_case(),
            equipment_exists_use_case=equipment_container.equipment_exists_use_case(),
            chat_use_case=chat_container.chat_use_case(),
            shop_item_repository_factory=shop_container.shop_item_repository_factory,
        )

        buy_command_handler = platform_container.buy_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_buy_name=self.container.config.bot.command_buy,
            economy_policy_factory=economy_container.economy_policy_factory,
            add_equipment_use_case=equipment_container.add_equipment_use_case(),
            equipment_exists_use_case=equipment_container.equipment_exists_use_case(),
            chat_use_case=chat_container.chat_use_case(),
            shop_item_repository_factory=shop_container.shop_item_repository_factory,
        )

        equipment_command_handler = platform_container.equipment_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_shop=self.container.config.bot.command_shop,
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
            chat_use_case=chat_container.chat_use_case(),
        )

        top_command_handler = platform_container.top_command_handler(
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
        )

        bottom_command_handler = platform_container.bottom_command_handler(
            economy_policy_factory=economy_container.economy_policy_factory, chat_use_case=chat_container.chat_use_case()
        )

        help_command_handler = platform_container.help_command_handler(
            command_prefix=self.container.config.bot.prefix,
            chat_use_case=chat_container.chat_use_case(),
            commands={
                self.container.config.bot.command_balance,
                self.container.config.bot.command_bonus,
                self.container.config.bot.command_roll,
                self.container.config.bot.command_transfer,
                self.container.config.bot.command_shop,
                self.container.config.bot.command_buy,
                self.container.config.bot.command_equipment,
                self.container.config.bot.command_top,
                self.container.config.bot.command_bottom,
                self.container.config.bot.command_stats,
                self.container.config.bot.command_fight,
                self.container.config.bot.command_gladdi,
                self.container.config.bot.command_followage,
            },
        )

        stats_command_handler = platform_container.stats_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_stats,
            economy_policy_factory=economy_container.economy_policy_factory,
            betting_service_factory=betting_container.betting_service_factory,
            battle_use_case=battle_container.battle_use_case(),
            chat_use_case=chat_container.chat_use_case(),
        )

        guess_number_command_handler = platform_container.guess_number_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_guess,
            minigame_repository=minigame_repository,
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
        )

        guess_letter_command_handler = platform_container.guess_letter_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_guess_letter,
            minigame_repository=minigame_repository,
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
        )

        guess_word_command_handler = platform_container.guess_word_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_guess_word,
            minigame_repository=minigame_repository,
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
        )

        rps_command_handler = platform_container.rps_command_handler(
            command_prefix=self.container.config.bot.prefix,
            command_name=self.container.config.bot.command_rps,
            minigame_repository=minigame_repository,
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
        )

        command_router: CommandRouter = CommandRouterImpl(self.container.config.bot.prefix)
        command_router.register_command_handler(self.container.config.bot.command_followage, followage_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_gladdi, ask_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_fight, battle_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_roll, roll_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_balance, balance_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_bonus, bonus_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_transfer, transfer_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_shop, shop_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_buy, buy_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_equipment, equipment_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_top, top_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_bottom, bottom_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_help, help_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_stats, stats_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_guess, guess_number_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_guess_letter, guess_letter_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_guess_word, guess_word_command_handler)
        command_router.register_command_handler(self.container.config.bot.command_rps, rps_command_handler)

        platform_chat_client = TwitchPlatformChatClient(
            handle_chat_message_use_case=HandleChatMessageUseCase(
                chat_message_uow=chat_message_uow_factory,
                get_intent_from_text_use_case_factory=ai_container.get_intent_from_text_use_case_factory,
                prompt_service=ai_container.prompt_service,
                generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
                db_ro_session=db_ro_session,
            ),
            handle_reply_use_case=HandleReplyUseCase(
                chat_message_uow=chat_message_uow_factory,
                prompt_service=ai_container.prompt_service,
                generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
                db_ro_session=db_ro_session,
            ),
            command_router=command_router,
            command_prefix=self.container.config.bot.prefix,
            help_command_handler=help_command_handler,
            logger=self.container.logger,
        )

        post_joke_job = joke_container.post_joke_job(
            send_channel_message=platform_chat_client.send_channel_message,
            conversation_service_factory=ai_container.conversation_service_factory,
            chat_use_case=chat_container.chat_use_case(),
            user_cache=viewer_cache,
            platform_repository=platform_repository,
            generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
        )

        stream_status_job = platform_container.stream_status_job(
            user_cache=viewer_cache,
            platform_repository=platform_repository,
            minigame_repository=minigame_repository,
            notification_repository=notification_container.notification_repository(),
            notification_group_id=self.container.config.telegram.group_id,
            generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
            state=chat_summary_state,
            stream_repository_factory=stream_container.stream_repository_factory,
            viewer_repository_factory=viewer_container.viewer_repository_factory,
            battle_use_case=battle_container.battle_use_case(),
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
            conversation_service_factory=ai_container.conversation_service_factory,
        )

        chat_summarizer_job = chat_container.chat_summarizer_job(
            stream_repository_factory=stream_container.stream_repository_factory,
            generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
            chat_summary_state=chat_summary_state,
        )

        minigame_job = MinigameTickJob(
            handle_minigame_tick_use_case=platform_container.handle_minigame_tick_use_case(
                minigame_repository=minigame_repository,
                economy_policy_factory=economy_container.economy_policy_factory,
                chat_use_case=chat_container.chat_use_case(),
                stream_repository_factory=stream_container.stream_repository_factory,
                get_used_words_use_case=minigame_container.get_used_words_use_case(),
                add_used_words_use_case=minigame_container.add_used_word_use_case(),
                conversation_service_factory=ai_container.conversation_service_factory,
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
                llm_repository_factory=ai_container.llm_repository_factory,
                prefix=self.container.config.bot.prefix,
                number_guess_name=self.container.config.bot.command_guess,
                command_guess_word=self.container.config.bot.command_guess_word,
                command_guess_letter=self.container.config.bot.command_guess_letter,
                rps_command_name=self.container.config.bot.command_rps,
                send_channel_message=platform_chat_client.send_channel_message,
            ),
            logger=self.container.logger,
        )

        viewer_time_job = platform_container.viewer_time_job(
            stream_repository_factory=stream_container.stream_repository_factory,
            viewer_repository_factory=viewer_container.viewer_repository_factory,
            economy_policy_factory=economy_container.economy_policy_factory,
            viewer_cache=viewer_cache,
            platform_repository=platform_repository,
        )

        followers_sync_job = platform_container.followers_sync_job(
            platform_repository=platform_repository, followers_repository_factory=follow_container.followers_repository_factory
        )

        jobs = [
            post_joke_job,
            platform_container.token_checker_job,
            stream_status_job,
            chat_summarizer_job,
            minigame_job,
            viewer_time_job,
            followers_sync_job,
        ]

        tasks = [Task(job.name, job.run) for job in jobs]
        task_runner = BackgroundTaskRunner(tasks)

        self.fast_api.state.bot_manager = BotManager(
            config=self.container.config.bot,
            telegram_config=self.container.config.telegram,
            llmbox_config=self.container.config.llmbox,
            intent_detector_config=self.container.config.intent_detector,
            logger=self.container.logger,
            minigame_repository=minigame_repository,
            get_used_word_use_case=minigame_container.get_used_words_use_case(),
            add_used_word_use_case=minigame_container.add_used_word_use_case(),
            stream_repository_factory=stream_container.stream_repository_factory,
            economy_policy_factory=economy_container.economy_policy_factory,
            chat_use_case=chat_container.chat_use_case(),
            followers_repository_factory=follow_container.followers_repository_factory,
            get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
            notification_repository=notification_container.notification_repository(),
            battle_use_case=battle_container.battle_use_case(),
            platform_container=platform_container,
            viewer_repository_factory=viewer_container.viewer_repository_factory,
            viewer_cache=viewer_cache,
            handle_restore_stream_use_case=HandleRestoreStreamContextUseCase(
                restore_stream_uow=platform_container.restore_stream_uow(
                    stream_repository_factory=stream_container.stream_repository_factory,
                ),
                minigame_repository=minigame_repository,
                logger=self.container.logger,
            ),
            platform_chat_client=platform_chat_client,
            chat_summarizer_job=chat_summarizer_job,
            post_joke_job=post_joke_job,
            stream_status_job=stream_status_job,
            token_checker_job=platform_container.token_checker_job,
            minigame_job=minigame_job,
            viewer_time_job=viewer_time_job,
            followers_sync_job=followers_sync_job,
            task_runner=task_runner,
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
