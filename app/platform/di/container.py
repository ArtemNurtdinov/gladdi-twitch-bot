from collections.abc import Awaitable, Callable

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.betting.application.betting_service import BettingService
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.domain.repo import ChatRepository
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.core.logger.domain.logger import Logger
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.follow.application.uow.followers_sync_uow import FollowersSyncUnitOfWorkFactory
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.follow.infrastructure.uow.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.uow.rps_uow import RpsUnitOfWorkFactory
from app.minigame.application.use_case.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.use_case.handle_rps_use_case import HandleRpsUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.infrastructure.uow.minigame_uow import SqlAlchemyMinigameUnitOfWorkFactory
from app.minigame.infrastructure.uow.rps_uow import SqlAlchemyRpsUnitOfWorkFactory
from app.moderation.application.chat_moderation_port import ChatModerationPort
from app.notification.domain.repository import NotificationRepository
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.auth.infrastructure.twitch_auth import TwitchAuth
from app.platform.command.bonus.application.bonus_command_handler import BonusCommandHandler
from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWorkFactory
from app.platform.command.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.platform.command.bonus.infrastructure.bonus_uow import SqlAlchemyBonusUnitOfWorkFactory
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.equipment.application.equipment_command_handler import EquipmentCommandHandler
from app.platform.command.equipment.application.equipment_uow import EquipmentUnitOfWorkFactory
from app.platform.command.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.platform.command.equipment.infrastructure.equipment_uow import SqlAlchemyEquipmentUnitOfWorkFactory
from app.platform.command.followage.application.followage_command_handler import FollowageCommandHandler
from app.platform.command.followage.application.uow import FollowAgeUnitOfWorkFactory
from app.platform.command.followage.application.usecase.handle_followage_use_case import HandleFollowAgeUseCase
from app.platform.command.followage.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.platform.command.guess.application.guess_letter_command_handler import GuessLetterCommandHandlerImpl
from app.platform.command.guess.application.guess_number_command_handler import GuessNumberCommandHandlerImpl
from app.platform.command.guess.application.guess_uow import GuessUnitOfWorkFactory
from app.platform.command.guess.application.guess_word_command_handler import GuessWordCommandHandlerImpl
from app.platform.command.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.platform.command.guess.application.rps_command_handler import RpsCommandHandlerImpl
from app.platform.command.guess.infrastructure.guess_uow import SqlAlchemyGuessUnitOfWorkFactory
from app.platform.command.help.application.handle_help_use_case import HandleHelpUseCase
from app.platform.command.help.application.help_uow import HelpUnitOfWorkFactory
from app.platform.command.help.infrastructure.help_command_handler import HelpCommandHandler
from app.platform.command.help.infrastructure.help_uow import SqlAlchemyHelpUnitOfWorkFactory
from app.platform.command.roll.application.handle_roll_use_case import HandleRollUseCase
from app.platform.command.roll.application.roll_command_handler import RollCommandHandler
from app.platform.command.roll.application.roll_uow import RollUnitOfWorkFactory
from app.platform.command.roll.infrastructure.roll_uow import SqlAlchemyRollUnitOfWorkFactory
from app.platform.command.shop.application.buy_command_handler import BuyCommandHandler
from app.platform.command.shop.application.handle_shop_use_case import HandleShopUseCase
from app.platform.command.shop.application.shop_command_handler import ShopCommandHandler
from app.platform.command.shop.application.shop_uow import ShopUnitOfWorkFactory
from app.platform.command.shop.infrastructure.shop_uow import SqlAlchemyShopUnitOfWorkFactory
from app.platform.command.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.platform.command.stats.application.stats_command_handler import StatsCommandHandlerImpl
from app.platform.command.stats.application.stats_uow import StatsUnitOfWorkFactory
from app.platform.command.stats.infrastructure.stats_uow import SqlAlchemyStatsUnitOfWorkFactory
from app.platform.command.top_bottom.application.bottom_command_handler import BottomCommandHandler
from app.platform.command.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.platform.command.top_bottom.application.top_bottom_uow import TopBottomUnitOfWorkFactory
from app.platform.command.top_bottom.application.top_command_handler import TopCommandHandler
from app.platform.command.top_bottom.infrastructure.top_bottom_uow import SqlAlchemyTopBottomUnitOfWorkFactory
from app.platform.command.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.platform.command.transfer.application.transfer_command_handler import TransferCommandHandler
from app.platform.command.transfer.application.transfer_uow import TransferUnitOfWorkFactory
from app.platform.command.transfer.infrastructure.transfer_uow import SqlAlchemyTransferUnitOfWorkFactory
from app.platform.domain.repository import PlatformRepository
from app.platform.infrastructure.api.client import TwitchHelixClient
from app.platform.infrastructure.repository import PlatformRepositoryImpl
from app.shop.domain.repository import ShopItemRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.uow.restore_stream_context_uow import RestoreStreamContextUnitOfWorkFactory
from app.stream.application.uow.stream_status_uow import StreamStatusUnitOfWorkFactory
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.uow.restore_stream_context_uow import SqlAlchemyRestoreStreamContextUnitOfWorkFactory
from app.stream.infrastructure.uow.stream_status_uow import SqlAlchemyStreamStatusUnitOfWorkFactory
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from app.viewer.session.application.job.viewer_time_job import ViewerTimeJob
from app.viewer.session.application.uow.viewer_time_uow import ViewerTimeUnitOfWorkFactory
from app.viewer.session.application.usecase.reward_viewer_time_use_case import RewardViewerTimeUseCase
from app.viewer.session.domain.repository import ViewerRepository
from app.viewer.session.infrastructure.uow.viewer_time_uow import SqlAlchemyViewerTimeUnitOfWorkFactory
from core.types import SessionFactory


class PlatformContainer:
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        client_id: str,
        client_secret: str,
        logger: Logger,
    ):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._logger = logger
        self.platform_auth = TwitchAuth(
            client_id=client_id,
            client_secret=client_secret,
            logger=logger,
        )
        self.api_client = TwitchHelixClient(self.platform_auth)
        self._handle_token_checker_use_case = HandleTokenCheckerUseCase(self.platform_auth, logger)
        self.token_checker_job = TokenCheckerJob(self._handle_token_checker_use_case, logger)

    def platform_repository(self) -> PlatformRepository:
        return PlatformRepositoryImpl(self.api_client, self._logger)

    def bonus_uow_factory(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> BonusUnitOfWorkFactory:
        return SqlAlchemyBonusUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_factory=stream_repository_factory,
            get_user_equipment_use_case=get_user_equipment_use_case,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
        )

    def handle_bonus_use_case(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> HandleBonusUseCase:
        bonus_uow_factory = self.bonus_uow_factory(
            stream_repository_factory, get_user_equipment_use_case, economy_policy_factory, chat_use_case
        )
        return HandleBonusUseCase(bonus_uow_factory)

    def bonus_command_handler(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> BonusCommandHandler:
        handle_bonus_use_case = self.handle_bonus_use_case(
            stream_repository_factory, get_user_equipment_use_case, economy_policy_factory, chat_use_case
        )
        return BonusCommandHandler(handle_bonus_use_case)

    def equipment_uow_factory(
        self, get_user_equipment_use_case: GetUserEquipmentUseCase, chat_use_case: ChatUseCase
    ) -> EquipmentUnitOfWorkFactory:
        return SqlAlchemyEquipmentUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            get_user_equipment_use_case=get_user_equipment_use_case,
            chat_use_case=chat_use_case,
        )

    def handle_equipment_use_case(
        self, get_user_equipment_use_case: GetUserEquipmentUseCase, chat_use_case: ChatUseCase
    ) -> HandleEquipmentUseCase:
        equipment_uow_factory = self.equipment_uow_factory(get_user_equipment_use_case, chat_use_case)
        return HandleEquipmentUseCase(equipment_uow_factory)

    def equipment_command_handler(
        self,
        command_prefix: str,
        command_shop: str,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
    ) -> EquipmentCommandHandler:
        handle_equipment_use_case = self.handle_equipment_use_case(get_user_equipment_use_case, chat_use_case)
        return EquipmentCommandHandler(
            command_prefix=command_prefix,
            command_shop=command_shop,
            handle_equipment_use_case=handle_equipment_use_case,
        )

    def guess_uow_factory(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> GuessUnitOfWorkFactory:
        return SqlAlchemyGuessUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
            get_user_equipment_use_case=get_user_equipment_use_case,
        )

    def handle_guess_use_case(
        self,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> HandleGuessUseCase:
        guess_uow_factory = self.guess_uow_factory(economy_policy_factory, chat_use_case, get_user_equipment_use_case)
        return HandleGuessUseCase(minigame_repository, guess_uow_factory)

    def guess_number_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_factory, chat_use_case, get_user_equipment_use_case
        )
        return GuessNumberCommandHandlerImpl(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case, bot_name=bot_name
        )

    def guess_letter_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_factory, chat_use_case, get_user_equipment_use_case
        )
        return GuessLetterCommandHandlerImpl(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case, bot_name=bot_name
        )

    def guess_word_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_factory, chat_use_case, get_user_equipment_use_case
        )
        return GuessWordCommandHandlerImpl(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case, bot_name=bot_name
        )

    def help_uow_factory(self, chat_use_case: ChatUseCase) -> HelpUnitOfWorkFactory:
        return SqlAlchemyHelpUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw, session_factory_ro=self._session_factory_ro, chat_use_case=chat_use_case
        )

    def handle_help_use_case(self, chat_use_case: ChatUseCase) -> HandleHelpUseCase:
        help_uow_factory = self.help_uow_factory(chat_use_case)
        return HandleHelpUseCase(help_uow_factory)

    def help_command_handler(self, command_prefix: str, chat_use_case: ChatUseCase, commands: set[str]) -> HelpCommandHandler:
        handle_help_use_case = self.handle_help_use_case(chat_use_case)
        return HelpCommandHandler(command_prefix=command_prefix, handle_help_use_case=handle_help_use_case, commands=commands)

    def roll_uow_factory(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        betting_service_factory: SessionScopedFactory[BettingService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
    ) -> RollUnitOfWorkFactory:
        return SqlAlchemyRollUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_factory=economy_policy_factory,
            betting_service_factory=betting_service_factory,
            get_user_equipment_use_case=get_user_equipment_use_case,
            chat_use_case=chat_use_case,
        )

    def handle_roll_use_case(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        betting_service_factory: SessionScopedFactory[BettingService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
        roll_cooldown_use_case: RollCooldownUseCase,
        calculate_timeout_use_case: CalculateTimeoutUseCase,
    ) -> HandleRollUseCase:
        roll_uow_factory = self.roll_uow_factory(
            economy_policy_factory, betting_service_factory, get_user_equipment_use_case, chat_use_case
        )
        return HandleRollUseCase(roll_uow_factory, roll_cooldown_use_case, calculate_timeout_use_case)

    def roll_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        betting_service_factory: SessionScopedFactory[BettingService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
        roll_cooldown_use_case: RollCooldownUseCase,
        calculate_timeout_use_case: CalculateTimeoutUseCase,
        chat_moderation_port: ChatModerationPort,
    ) -> RollCommandHandler:
        handle_roll_use_case = self.handle_roll_use_case(
            economy_policy_factory,
            betting_service_factory,
            get_user_equipment_use_case,
            chat_use_case,
            roll_cooldown_use_case,
            calculate_timeout_use_case,
        )
        return RollCommandHandler(
            command_prefix=command_prefix,
            command_name=command_name,
            handle_roll_use_case=handle_roll_use_case,
            chat_moderation=chat_moderation_port,
        )

    def shop_uow_factory(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_factory: SessionScopedFactory[ShopItemRepository],
    ) -> ShopUnitOfWorkFactory:
        return SqlAlchemyShopUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_factory=economy_policy_factory,
            add_equipment_use_case=add_equipment_use_case,
            equipment_exists_use_case=equipment_exists_use_case,
            chat_use_case=chat_use_case,
            shop_item_repository_factory=shop_item_repository_factory,
        )

    def handle_shop_use_case(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_factory: SessionScopedFactory[ShopItemRepository],
    ) -> HandleShopUseCase:
        shop_uow_factory = self.shop_uow_factory(
            economy_policy_factory, add_equipment_use_case, equipment_exists_use_case, chat_use_case, shop_item_repository_factory
        )
        return HandleShopUseCase(shop_uow_factory)

    def shop_command_handler(
        self,
        command_prefix: str,
        command_shop_name: str,
        command_buy_name: str,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_factory: SessionScopedFactory[ShopItemRepository],
    ) -> ShopCommandHandler:
        handle_shop_use_case = self.handle_shop_use_case(
            economy_policy_factory, add_equipment_use_case, equipment_exists_use_case, chat_use_case, shop_item_repository_factory
        )
        return ShopCommandHandler(
            command_prefix=command_prefix,
            command_shop_name=command_shop_name,
            command_buy_name=command_buy_name,
            handle_shop_use_case=handle_shop_use_case,
        )

    def buy_command_handler(
        self,
        command_prefix: str,
        command_buy_name: str,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_factory: SessionScopedFactory[ShopItemRepository],
    ) -> BuyCommandHandler:
        handle_shop_use_case = self.handle_shop_use_case(
            economy_policy_factory, add_equipment_use_case, equipment_exists_use_case, chat_use_case, shop_item_repository_factory
        )
        return BuyCommandHandler(
            command_prefix=command_prefix, command_buy_name=command_buy_name, handle_shop_use_case=handle_shop_use_case
        )

    def stats_uow_factory(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        betting_service_factory: SessionScopedFactory[BettingService],
        battle_use_case: BattleUseCase,
        chat_use_case: ChatUseCase,
    ) -> StatsUnitOfWorkFactory:
        return SqlAlchemyStatsUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_factory=economy_policy_factory,
            betting_service_factory=betting_service_factory,
            battle_use_case=battle_use_case,
            chat_use_case=chat_use_case,
        )

    def handle_stats_use_case(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        betting_service_factory: SessionScopedFactory[BettingService],
        battle_use_case: BattleUseCase,
        chat_use_case: ChatUseCase,
    ) -> HandleStatsUseCase:
        stats_uow_factory = self.stats_uow_factory(economy_policy_factory, betting_service_factory, battle_use_case, chat_use_case)
        return HandleStatsUseCase(stats_uow_factory)

    def stats_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        betting_service_factory: SessionScopedFactory[BettingService],
        battle_use_case: BattleUseCase,
        chat_use_case: ChatUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_stats_use_case = self.handle_stats_use_case(economy_policy_factory, betting_service_factory, battle_use_case, chat_use_case)
        return StatsCommandHandlerImpl(
            command_prefix=command_prefix, command_name=command_name, handle_stats_use_case=handle_stats_use_case, bot_name=bot_name
        )

    def top_bottom_uow_factory(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> TopBottomUnitOfWorkFactory:
        return SqlAlchemyTopBottomUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
        )

    def handle_top_bottom_use_case(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> HandleTopBottomUseCase:
        top_bottom_uow_factory = self.top_bottom_uow_factory(economy_policy_factory, chat_use_case)
        return HandleTopBottomUseCase(top_bottom_uow_factory)

    def top_command_handler(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> TopCommandHandler:
        handle_top_bottom_use_case = self.handle_top_bottom_use_case(economy_policy_factory, chat_use_case)
        return TopCommandHandler(handle_top_bottom_use_case)

    def bottom_command_handler(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> BottomCommandHandler:
        handle_top_bottom_use_case = self.handle_top_bottom_use_case(economy_policy_factory, chat_use_case)
        return BottomCommandHandler(handle_top_bottom_use_case)

    def transfer_uow_factory(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> TransferUnitOfWorkFactory:
        return SqlAlchemyTransferUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
        )

    def handle_transfer_use_case(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> HandleTransferUseCase:
        transfer_uow_factory = self.transfer_uow_factory(economy_policy_factory, chat_use_case)
        return HandleTransferUseCase(transfer_uow_factory)

    def transfer_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> TransferCommandHandler:
        handle_transfer_use_case = self.handle_transfer_use_case(economy_policy_factory, chat_use_case)
        return TransferCommandHandler(
            command_prefix=command_prefix, command_name=command_name, handle_transfer_use_case=handle_transfer_use_case
        )

    def minigame_uow_factory(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        get_used_words_use_case: GetUsedWordsUseCase,
        add_used_words_use_case: AddUsedWordsUseCase,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> MinigameUnitOfWorkFactory:
        return SqlAlchemyMinigameUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
            stream_repository_factory=stream_repository_factory,
            get_used_words_use_case=get_used_words_use_case,
            add_used_words_use_case=add_used_words_use_case,
            conversation_service_factory=conversation_service_factory,
            get_user_equipment_use_case=get_user_equipment_use_case,
        )

    def start_word_game_use_case(
        self,
        prefix: str,
        minigame_repository: MinigameRepository,
        minigame_uow_factory: MinigameUnitOfWorkFactory,
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        llm_repository_factory: SessionScopedFactory[LLMRepository],
        command_guess_word: str,
        command_guess_letter: str,
        send_channel_message: Callable[[str], Awaitable[None]],
        bot_name: str,
    ) -> StartWordGameUseCase:
        return StartWordGameUseCase(
            minigame_repository,
            prefix,
            minigame_uow_factory,
            self._session_factory_ro,
            system_prompt_repository_factory,
            llm_repository_factory,
            command_guess_word,
            command_guess_letter,
            send_channel_message,
            bot_name,
            self._logger,
        )

    def start_number_guess_game_use_case(
        self,
        prefix: str,
        minigame_repository: MinigameRepository,
        minigame_uow_factory: MinigameUnitOfWorkFactory,
        command_name: str,
        send_channel_message: Callable[[str], Awaitable[None]],
        bot_name: str,
    ) -> StartNumberGuessGameUseCase:
        return StartNumberGuessGameUseCase(minigame_repository, prefix, command_name, send_channel_message, minigame_uow_factory, bot_name)

    def start_rps_game_use_case(
        self,
        prefix: str,
        minigame_repository: MinigameRepository,
        minigame_uow_factory: MinigameUnitOfWorkFactory,
        command_name: str,
        send_channel_message: Callable[[str], Awaitable[None]],
        bot_name: str,
    ) -> StartRpsGameUseCase:
        return StartRpsGameUseCase(minigame_repository, prefix, command_name, send_channel_message, minigame_uow_factory, bot_name)

    def finish_rps_game_use_case(
        self,
        minigame_repository: MinigameRepository,
        minigame_uow_factory: MinigameUnitOfWorkFactory,
        bot_name: str,
        send_channel_message: Callable[[str], Awaitable[None]],
    ) -> FinishRpsUseCase:
        return FinishRpsUseCase(minigame_repository, minigame_uow_factory, bot_name, send_channel_message)

    def finish_expired_games_use_case(
        self,
        minigame_repository: MinigameRepository,
        minigame_uow_factory: MinigameUnitOfWorkFactory,
        send_channel_message: Callable[[str], Awaitable[None]],
        bot_name: str,
    ) -> FinishExpiredGamesUseCase:
        return FinishExpiredGamesUseCase(minigame_repository, send_channel_message, minigame_uow_factory, bot_name)

    def handle_minigame_tick_use_case(
        self,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        get_used_words_use_case: GetUsedWordsUseCase,
        add_used_words_use_case: AddUsedWordsUseCase,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        llm_repository_factory: SessionScopedFactory[LLMRepository],
        prefix: str,
        number_guess_name: str,
        command_guess_word: str,
        command_guess_letter: str,
        rps_command_name: str,
        send_channel_message: Callable[[str], Awaitable[None]],
        bot_name: str,
    ) -> HandleMinigameTickUseCase:
        minigame_uow_factory = self.minigame_uow_factory(
            economy_policy_factory,
            chat_use_case,
            stream_repository_factory,
            get_used_words_use_case,
            add_used_words_use_case,
            conversation_service_factory,
            get_user_equipment_use_case,
        )
        start_number_guess_game_use_case = self.start_number_guess_game_use_case(
            prefix, minigame_repository, minigame_uow_factory, number_guess_name, send_channel_message, bot_name
        )
        start_word_game_use_case = self.start_word_game_use_case(
            prefix,
            minigame_repository,
            minigame_uow_factory,
            system_prompt_repository_factory,
            llm_repository_factory,
            command_guess_word,
            command_guess_letter,
            send_channel_message,
            bot_name,
        )
        start_rps_game_use_case = self.start_rps_game_use_case(
            prefix, minigame_repository, minigame_uow_factory, rps_command_name, send_channel_message, bot_name
        )
        finish_rps_game_use_case = self.finish_rps_game_use_case(minigame_repository, minigame_uow_factory, bot_name, send_channel_message)
        finish_expired_games_use_case = self.finish_expired_games_use_case(
            minigame_repository, minigame_uow_factory, send_channel_message, bot_name
        )
        return HandleMinigameTickUseCase(
            minigame_repository,
            minigame_uow_factory,
            start_number_guess_game_use_case,
            start_word_game_use_case,
            start_rps_game_use_case,
            finish_rps_game_use_case,
            finish_expired_games_use_case,
        )

    def rps_uow_factory(
        self, economy_policy_factory: SessionScopedFactory[EconomyPolicy], chat_use_case: ChatUseCase
    ) -> RpsUnitOfWorkFactory:
        return SqlAlchemyRpsUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
        )

    def handle_rps_use_case(
        self,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> HandleRpsUseCase:
        rps_uow_factory = self.rps_uow_factory(economy_policy_factory, chat_use_case)
        return HandleRpsUseCase(minigame_repository, rps_uow_factory)

    def rps_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_rps_use_case = self.handle_rps_use_case(minigame_repository, economy_policy_factory, chat_use_case)
        return RpsCommandHandlerImpl(command_prefix, command_name, handle_rps_use_case, bot_name)

    def follow_age_uow_factory(
        self,
        chat_repository_factory: SessionScopedFactory[ChatRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        platform_repository: PlatformRepository,
    ) -> FollowAgeUnitOfWorkFactory:
        return SqlAlchemyFollowAgeUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            chat_repository_factory=chat_repository_factory,
            conversation_service_factory=conversation_service_factory,
            system_prompt_repository_factory=system_prompt_repository_factory,
            platform_repository=platform_repository,
        )

    def handle_follow_age_use_case(
        self,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        chat_repository_factory: SessionScopedFactory[ChatRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        platform_repository: PlatformRepository,
    ) -> HandleFollowAgeUseCase:
        follow_age_uow_factory = self.follow_age_uow_factory(
            chat_repository_factory, conversation_service_factory, system_prompt_repository_factory, platform_repository
        )
        return HandleFollowAgeUseCase(generate_response_use_case_factory, follow_age_uow_factory, self._session_factory_ro)

    def followage_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        chat_repository_factory: SessionScopedFactory[ChatRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        platform_repository: PlatformRepository,
    ) -> FollowageCommandHandler:
        handle_follow_age_use_case = self.handle_follow_age_use_case(
            generate_response_use_case_factory,
            chat_repository_factory,
            conversation_service_factory,
            system_prompt_repository_factory,
            platform_repository,
        )
        return FollowageCommandHandler(
            command_prefix=command_prefix,
            command_name=command_name,
            handle_follow_age_use_case=handle_follow_age_use_case,
        )

    def sync_followers_uow_factory(
        self, followers_repository_factory: SessionScopedFactory[FollowersRepository]
    ) -> FollowersSyncUnitOfWorkFactory:
        return SqlAlchemyFollowersSyncUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            followers_repository_factory=followers_repository_factory,
        )

    def handle_followers_sync_use_case(
        self, platform_repository: PlatformRepository, followers_repository_factory: SessionScopedFactory[FollowersRepository]
    ) -> HandleFollowersSyncUseCase:
        sync_followers_uow_factory = self.sync_followers_uow_factory(followers_repository_factory)
        return HandleFollowersSyncUseCase(platform_repository, sync_followers_uow_factory)

    def followers_sync_job(
        self,
        channel_name: str,
        platform_repository: PlatformRepository,
        followers_repository_factory: SessionScopedFactory[FollowersRepository],
    ) -> FollowersSyncJob:
        handle_followers_sync_use_case = self.handle_followers_sync_use_case(platform_repository, followers_repository_factory)
        return FollowersSyncJob(channel_name, handle_followers_sync_use_case, self._logger)

    def restore_stream_uow(
        self, stream_repository_factory: SessionScopedFactory[StreamRepository]
    ) -> RestoreStreamContextUnitOfWorkFactory:
        return SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_factory=stream_repository_factory,
        )

    def stream_status_uow_factory(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        battle_use_case: BattleUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        conversation_service_factory: SessionScopedFactory[ConversationService],
    ) -> StreamStatusUnitOfWorkFactory:
        return SqlAlchemyStreamStatusUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            stream_repository_factory=stream_repository_factory,
            viewer_repository_factory=viewer_repository_factory,
            battle_use_case=battle_use_case,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
            conversation_service_factory=conversation_service_factory,
        )

    def handle_stream_status_use_case(
        self,
        user_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
        minigame_repository: MinigameRepository,
        notification_repository: NotificationRepository,
        notification_group_id: int,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        state: ChatSummaryState,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        battle_use_case: BattleUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        conversation_service_factory: SessionScopedFactory[ConversationService],
    ) -> HandleStreamStatusUseCase:
        stream_status_uow_factory = self.stream_status_uow_factory(
            stream_repository_factory,
            viewer_repository_factory,
            battle_use_case,
            economy_policy_factory,
            chat_use_case,
            conversation_service_factory,
        )
        return HandleStreamStatusUseCase(
            user_cache,
            platform_repository,
            stream_status_uow_factory,
            minigame_repository,
            notification_repository,
            notification_group_id,
            generate_response_use_case_factory,
            state,
            self._session_factory_ro,
            self._logger,
        )

    def stream_status_job(
        self,
        channel_name: str,
        user_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
        minigame_repository: MinigameRepository,
        notification_repository: NotificationRepository,
        notification_group_id: int,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        state: ChatSummaryState,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        battle_use_case: BattleUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        conversation_service_factory: SessionScopedFactory[ConversationService],
    ) -> StreamStatusJob:
        handle_stream_status_use_case = self.handle_stream_status_use_case(
            user_cache=user_cache,
            platform_repository=platform_repository,
            minigame_repository=minigame_repository,
            notification_repository=notification_repository,
            notification_group_id=notification_group_id,
            generate_response_use_case_factory=generate_response_use_case_factory,
            state=state,
            stream_repository_factory=stream_repository_factory,
            viewer_repository_factory=viewer_repository_factory,
            battle_use_case=battle_use_case,
            economy_policy_factory=economy_policy_factory,
            chat_use_case=chat_use_case,
            conversation_service_factory=conversation_service_factory,
        )
        return StreamStatusJob(channel_name, handle_stream_status_use_case, self._logger)

    def reward_viewer_time_uow_factory(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
    ) -> ViewerTimeUnitOfWorkFactory:
        return SqlAlchemyViewerTimeUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_factory=stream_repository_factory,
            viewer_repository_factory=viewer_repository_factory,
            economy_policy_factory=economy_policy_factory,
        )

    def handle_viewer_time_use_case(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        viewer_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
    ) -> RewardViewerTimeUseCase:
        reward_viewer_time_uow_factory = self.reward_viewer_time_uow_factory(
            stream_repository_factory, viewer_repository_factory, economy_policy_factory
        )
        return RewardViewerTimeUseCase(reward_viewer_time_uow_factory, viewer_cache, platform_repository)

    def viewer_time_job(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        viewer_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
        channel_name: str,
        bot_name: str,
    ) -> ViewerTimeJob:
        handle_viewer_time_use_case = self.handle_viewer_time_use_case(
            stream_repository_factory, viewer_repository_factory, economy_policy_factory, viewer_cache, platform_repository
        )
        return ViewerTimeJob(channel_name, handle_viewer_time_use_case, bot_name, self._logger)
