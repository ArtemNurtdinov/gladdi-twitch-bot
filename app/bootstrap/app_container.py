from app.ai.gen.di.container import AIContainer
from app.auth.di.container import AuthContainer
from app.battle.di.container import BattleContainer
from app.betting.di.container import BettingContainer
from app.bootstrap.command_registry import CommandRegistry
from app.bootstrap.model.command_registry_deps import CommandRegistryDeps
from app.bot.bot_manager import BotManager
from app.bot.bot_manager_factory import BotManagerFactory
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.di.container import ChatContainer
from app.common.infrastructure.db.db import db_ro_session, db_rw_session
from app.common.infrastructure.db.session_scoped_factory import SessionScopedFactory
from app.core.config.domain.model.configuration import Config
from app.core.di.application_container import ApplicationContainer
from app.core.logger.domain.logger import Logger
from app.economy.di.container import EconomyContainer
from app.equipment.di.container import EquipmentContainer
from app.follow.di.container import FollowContainer
from app.joke.di.container import JokeContainer
from app.minigame.di.container import MinigameContainer
from app.notification.di.container import NotificationContainer
from app.platform.application.timeout_use_case import TimeoutUseCase
from app.platform.chat.application.usecase.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.usecase.handle_reply_use_case import HandleReplyUseCase
from app.platform.chat.infrastructure.twitch_platform_client import TwitchPlatformChatClient
from app.platform.command.ask.di.container import AskContainer
from app.platform.command.domain.command_router import CommandRouter
from app.platform.command.help.infrastructure.help_command_handler import HelpCommandHandler
from app.platform.di.container import PlatformContainer
from app.shop.di.container import ShopContainer
from app.stream.di.container import StreamContainer
from app.viewer.di.container import ViewerContainer
from app.viewer.infrastructure.cache.viewer_cache_service import ViewerCacheService


class AppContainer:
    def __init__(self, core: ApplicationContainer):
        self.core = core
        self.config: Config = core.config
        self.logger: Logger = core.logger

        self.auth = AuthContainer(self.config.application)
        self.joke = JokeContainer(
            session_factory_ro=db_ro_session,
            session_factory_rw=db_rw_session,
            logger=self.logger,
        )
        self.ai = AIContainer(
            session_factory_ro=db_ro_session,
            session_factory_rw=db_rw_session,
            llmbox_host=self.config.llmbox.host,
            intent_detector_host=self.config.intent_detector.host,
        )
        self.shop = ShopContainer()
        self.stream = StreamContainer()
        self.chat = ChatContainer(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            logger=self.logger,
        )
        self.economy = EconomyContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
        self.follow = FollowContainer()
        self.betting = BettingContainer()
        self.ask = AskContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
        self.equipment = EquipmentContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
        self.minigame = MinigameContainer(
            session_factory_ro=db_ro_session,
            session_factory_rw=db_rw_session,
            logger=self.logger,
        )
        self.notification = NotificationContainer(
            tg_bot_token=self.config.telegram.bot_token,
            logger=self.logger,
            proxy_url=self.config.telegram.proxy_url,
        )
        self.battle = BattleContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
        self.viewer = ViewerContainer()
        self.platform = PlatformContainer(
            client_id=self.config.twitch.client_id,
            client_secret=self.config.twitch.client_secret,
            session_factory_ro=db_ro_session,
            session_factory_rw=db_rw_session,
            logger=self.logger,
        )

        platform_repository = self.platform.platform_repository()
        viewer_cache = ViewerCacheService(platform_repository)
        moderation_service = TimeoutUseCase(
            platform_repository=platform_repository,
            viewer_cache=viewer_cache,
            logger=self.logger,
        )
        chat_summary_state = ChatSummaryState()
        minigame_repository = self.minigame.minigame_repository()

        commands = CommandRegistry(
            CommandRegistryDeps(
                bot=self.config.bot,
                platform=self.platform,
                chat=self.chat,
                ai=self.ai,
                ask=self.ask,
                battle=self.battle,
                economy=self.economy,
                equipment=self.equipment,
                betting=self.betting,
                stream=self.stream,
                shop=self.shop,
            ),
            platform_repository=platform_repository,
            minigame_repository=minigame_repository,
            moderation_service=moderation_service,
        ).build()
        platform_chat_client = self._build_platform_chat_client(
            command_router=commands.router,
            help_command_handler=commands.help_command_handler,
        )
        self.bot_manager = self._build_bot_manager(
            platform_repository=platform_repository,
            minigame_repository=minigame_repository,
            platform_chat_client=platform_chat_client,
            viewer_cache=viewer_cache,
            chat_summary_state=chat_summary_state,
        )

    @classmethod
    def create(cls, core: ApplicationContainer | None = None) -> "AppContainer":
        return cls(core or ApplicationContainer())

    def _build_platform_chat_client(
        self,
        command_router: CommandRouter,
        help_command_handler: HelpCommandHandler,
    ) -> TwitchPlatformChatClient:
        chat_message_uow_factory = self.chat.chat_message_uow_factory(
            economy_policy_factory=self.economy.economy_policy_factory,
            stream_repository_factory=self.stream.stream_repository_factory,
            viewer_repository_factory=self.viewer.viewer_repository_factory,
            conversation_service_factory=self.ai.conversation_service_factory,
            system_prompt_repository_factory=self.ai.system_prompt_repository_factory,
        )

        return TwitchPlatformChatClient(
            handle_chat_message_use_case=HandleChatMessageUseCase(
                chat_message_uow=chat_message_uow_factory,
                get_intent_from_text_use_case_factory=self.ai.get_intent_from_text_use_case_factory,
                prompt_service=self.ai.prompt_service,
                generate_response_use_case_factory=self.ai.generate_response_use_case_factory,
                db_ro_session=db_ro_session,
            ),
            handle_reply_use_case=HandleReplyUseCase(
                chat_message_uow=chat_message_uow_factory,
                prompt_service=self.ai.prompt_service,
                generate_response_use_case_factory=self.ai.generate_response_use_case_factory,
                db_ro_session=db_ro_session,
            ),
            command_router=command_router,
            command_prefix=self.config.bot.prefix,
            help_command_handler=help_command_handler,
            logger=self.logger,
        )

    def _build_bot_manager(
        self,
        platform_repository,
        minigame_repository,
        platform_chat_client: TwitchPlatformChatClient,
        viewer_cache: ViewerCacheService,
        chat_summary_state: ChatSummaryState,
    ) -> BotManager:
        bot_manager_factory = BotManagerFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            platform_repository=platform_repository,
            stream_repository_factory=self.stream.stream_repository_factory,
            minigame_repository=minigame_repository,
            platform_chat_client=platform_chat_client,
            chat_repository_factory=self.chat.chat_repository_factory,
            generate_response_use_case_factory=self.ai.generate_response_use_case_factory,
            chat_summary_state=chat_summary_state,
            conversation_service_factory=self.ai.conversation_service_factory,
            jokes_configuration_repository_factory=SessionScopedFactory(self.joke.jokes_configuration_repository),
            viewer_repository_factory=self.viewer.viewer_repository_factory,
            battle_use_case=self.battle.battle_use_case(),
            economy_policy_factory=self.economy.economy_policy_factory,
            notification_repository=self.notification.notification_repository(),
            notification_group_id=self.config.telegram.group_id,
            get_used_words_use_case=self.minigame.get_used_words_use_case(),
            add_used_words_use_case=self.minigame.add_used_word_use_case(),
            get_user_equipment_use_case=self.equipment.get_user_equipment_use_case(),
            prefix=self.config.bot.prefix,
            guess_number_command_name=self.config.bot.command_guess,
            system_prompt_repository_factory=self.ai.system_prompt_repository_factory,
            llm_repository_factory=self.ai.llm_repository_factory,
            command_guess_word=self.config.bot.command_guess_word,
            command_guess_letter=self.config.bot.command_guess_letter,
            rps_command_name=self.config.bot.command_rps,
            followers_repository_factory=self.follow.followers_repository_factory,
            platform_auth=self.platform.platform_auth,
            api_client=self.platform.api_client,
            viewer_cache=viewer_cache,
            prompt_service=self.ai.prompt_service,
            logger=self.logger,
        )
        return bot_manager_factory.create()
