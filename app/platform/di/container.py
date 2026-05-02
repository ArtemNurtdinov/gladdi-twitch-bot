from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.betting.application.betting_service import BettingService
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
from app.minigame.application.uow.rps_uow import RpsUnitOfWorkFactory
from app.minigame.application.use_case.handle_rps_use_case import HandleRpsUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.infrastructure.uow.rps_uow import SqlAlchemyRpsUnitOfWorkFactory
from app.moderation.application.timeout_use_case import TimeoutUseCase
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.auth.infrastructure.twitch_auth import TwitchAuth
from app.platform.command.bonus.application.bonus_command_handler import BonusCommandHandler
from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWorkFactory
from app.platform.command.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.platform.command.bonus.infrastructure.bonus_uow import SqlAlchemyBonusUnitOfWorkFactory
from app.platform.command.equipment.application.equipment_command_handler import EquipmentCommandHandler
from app.platform.command.equipment.application.equipment_uow import EquipmentUnitOfWorkFactory
from app.platform.command.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.platform.command.equipment.infrastructure.equipment_uow import SqlAlchemyEquipmentUnitOfWorkFactory
from app.platform.command.followage.application.followage_command_handler import FollowageCommandHandler
from app.platform.command.followage.application.uow import FollowAgeUnitOfWorkFactory
from app.platform.command.followage.application.usecase.handle_followage_use_case import HandleFollowAgeUseCase
from app.platform.command.followage.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.platform.command.guess.application.guess_letter_command_handler import GuessLetterCommandHandler
from app.platform.command.guess.application.guess_number_command_handler import GuessNumberCommandHandler
from app.platform.command.guess.application.guess_uow import GuessUnitOfWorkFactory
from app.platform.command.guess.application.guess_word_command_handler import GuessWordCommandHandler
from app.platform.command.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.platform.command.guess.application.rps_command_handler import RpsCommandHandler
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
from app.platform.command.stats.application.stats_command_handler import StatsCommandHandler
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
from app.stream.domain.repo import StreamRepository
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
    ) -> GuessNumberCommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_factory, chat_use_case, get_user_equipment_use_case
        )
        return GuessNumberCommandHandler(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case
        )

    def guess_letter_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> GuessLetterCommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_factory, chat_use_case, get_user_equipment_use_case
        )
        return GuessLetterCommandHandler(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case
        )

    def guess_word_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> GuessWordCommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_factory, chat_use_case, get_user_equipment_use_case
        )
        return GuessWordCommandHandler(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case
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
        timeout_use_case: TimeoutUseCase,
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
            timeout_use_case=timeout_use_case,
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
    ) -> StatsCommandHandler:
        handle_stats_use_case = self.handle_stats_use_case(economy_policy_factory, betting_service_factory, battle_use_case, chat_use_case)
        return StatsCommandHandler(command_prefix=command_prefix, command_name=command_name, handle_stats_use_case=handle_stats_use_case)

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
    ) -> RpsCommandHandler:
        handle_rps_use_case = self.handle_rps_use_case(minigame_repository, economy_policy_factory, chat_use_case)
        return RpsCommandHandler(command_prefix, command_name, handle_rps_use_case)

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
