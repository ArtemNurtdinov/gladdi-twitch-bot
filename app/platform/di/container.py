from app.betting.application.betting_service import BettingService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.moderation.application.chat_moderation_port import ChatModerationPort
from app.platform.command.bonus.application.bonus_command_handler import BonusCommandHandlerImpl
from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWorkFactory
from app.platform.command.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.platform.command.bonus.infrastructure.bonus_uow import SqlAlchemyBonusUnitOfWorkFactory
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.equipment.application.equipment_command_handler import EquipmentCommandHandlerImpl
from app.platform.command.equipment.application.equipment_uow import EquipmentUnitOfWorkFactory
from app.platform.command.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.platform.command.equipment.infrastructure.equipment_uow import SqlAlchemyEquipmentUnitOfWorkFactory
from app.platform.command.guess.application.guess_letter_command_handler import GuessLetterCommandHandlerImpl
from app.platform.command.guess.application.guess_number_command_handler import GuessNumberCommandHandlerImpl
from app.platform.command.guess.application.guess_uow import GuessUnitOfWorkFactory
from app.platform.command.guess.application.guess_word_command_handler import GuessWordCommandHandlerImpl
from app.platform.command.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.platform.command.guess.infrastructure.guess_uow import SqlAlchemyGuessUnitOfWorkFactory
from app.platform.command.help.application.handle_help_use_case import HandleHelpUseCase
from app.platform.command.help.application.help_uow import HelpUnitOfWorkFactory
from app.platform.command.help.infrastructure.help_command_handler import HelpCommandHandlerImpl
from app.platform.command.help.infrastructure.help_uow import SqlAlchemyHelpUnitOfWorkFactory
from app.platform.command.roll.application.handle_roll_use_case import HandleRollUseCase
from app.platform.command.roll.application.roll_command_handler import RollCommandHandlerImpl
from app.platform.command.roll.application.roll_uow import RollUnitOfWorkFactory
from app.platform.command.roll.infrastructure.roll_uow import SqlAlchemyRollUnitOfWorkFactory
from app.platform.command.shop.application.buy_command_handler import BuyCommandHandlerImpl
from app.platform.command.shop.application.handle_shop_use_case import HandleShopUseCase
from app.platform.command.shop.application.shop_command_handler import ShopCommandHandlerImpl
from app.platform.command.shop.application.shop_uow import ShopUnitOfWorkFactory
from app.platform.command.shop.infrastructure.shop_uow import SqlAlchemyShopUnitOfWorkFactory
from app.shop.domain.repository import ShopItemRepository
from app.stream.domain.repo import StreamRepository
from core.provider import Provider
from core.types import SessionFactory


class PlatformContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro

    def bonus_uow_factory(
        self,
        stream_repository_provider: Provider[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> BonusUnitOfWorkFactory:
        return SqlAlchemyBonusUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_provider=stream_repository_provider,
            get_user_equipment_use_case=get_user_equipment_use_case,
            economy_policy_provider=economy_policy_provider,
            chat_use_case=chat_use_case,
        )

    def handle_bonus_use_case(
        self,
        stream_repository_provider: Provider[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ) -> HandleBonusUseCase:
        bonus_uow_factory = self.bonus_uow_factory(
            stream_repository_provider, get_user_equipment_use_case, economy_policy_provider, chat_use_case
        )
        return HandleBonusUseCase(bonus_uow_factory)

    def bonus_command_handler(
        self,
        stream_repository_provider: Provider[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_bonus_use_case = self.handle_bonus_use_case(
            stream_repository_provider, get_user_equipment_use_case, economy_policy_provider, chat_use_case
        )
        return BonusCommandHandlerImpl(handle_bonus_use_case, bot_name)

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
        bot_name: str,
    ) -> CommandHandler:
        handle_equipment_use_case = self.handle_equipment_use_case(get_user_equipment_use_case, chat_use_case)
        return EquipmentCommandHandlerImpl(
            command_prefix=command_prefix,
            command_shop=command_shop,
            handle_equipment_use_case=handle_equipment_use_case,
            bot_name=bot_name,
        )

    def guess_uow_factory(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> GuessUnitOfWorkFactory:
        return SqlAlchemyGuessUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            economy_policy_provider=economy_policy_provider,
            chat_use_case=chat_use_case,
            get_user_equipment_use_case=get_user_equipment_use_case,
        )

    def handle_guess_use_case(
        self,
        minigame_repository: MinigameRepository,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> HandleGuessUseCase:
        guess_uow_factory = self.guess_uow_factory(economy_policy_provider, chat_use_case, get_user_equipment_use_case)
        return HandleGuessUseCase(minigame_repository, guess_uow_factory)

    def guess_number_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_provider, chat_use_case, get_user_equipment_use_case
        )
        return GuessNumberCommandHandlerImpl(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case, bot_name=bot_name
        )

    def guess_letter_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_provider, chat_use_case, get_user_equipment_use_case
        )
        return GuessLetterCommandHandlerImpl(
            command_prefix=command_prefix, command_name=command_name, handle_guess_use_case=handle_guess_use_case, bot_name=bot_name
        )

    def guess_word_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        minigame_repository: MinigameRepository,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        bot_name: str,
    ) -> CommandHandler:
        handle_guess_use_case = self.handle_guess_use_case(
            minigame_repository, economy_policy_provider, chat_use_case, get_user_equipment_use_case
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

    def help_command_handler(self, command_prefix: str, chat_use_case: ChatUseCase, commands: set[str], bot_name: str) -> CommandHandler:
        handle_help_use_case = self.handle_help_use_case(chat_use_case)
        return HelpCommandHandlerImpl(
            command_prefix=command_prefix, handle_help_use_case=handle_help_use_case, commands=commands, bot_name=bot_name
        )

    def roll_uow_factory(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        betting_service_provider: Provider[BettingService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
    ) -> RollUnitOfWorkFactory:
        return SqlAlchemyRollUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_provider=economy_policy_provider,
            betting_service_provider=betting_service_provider,
            get_user_equipment_use_case=get_user_equipment_use_case,
            chat_use_case=chat_use_case,
        )

    def handle_roll_use_case(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        betting_service_provider: Provider[BettingService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
        roll_cooldown_use_case: RollCooldownUseCase,
        calculate_timeout_use_case: CalculateTimeoutUseCase,
    ) -> HandleRollUseCase:
        roll_uow_factory = self.roll_uow_factory(
            economy_policy_provider, betting_service_provider, get_user_equipment_use_case, chat_use_case
        )
        return HandleRollUseCase(roll_uow_factory, roll_cooldown_use_case, calculate_timeout_use_case)

    def roll_command_handler(
        self,
        command_prefix: str,
        command_name: str,
        economy_policy_provider: Provider[EconomyPolicy],
        betting_service_provider: Provider[BettingService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
        roll_cooldown_use_case: RollCooldownUseCase,
        calculate_timeout_use_case: CalculateTimeoutUseCase,
        chat_moderation_port: ChatModerationPort,
        bot_name: str,
    ) -> CommandHandler:
        handle_roll_use_case = self.handle_roll_use_case(
            economy_policy_provider,
            betting_service_provider,
            get_user_equipment_use_case,
            chat_use_case,
            roll_cooldown_use_case,
            calculate_timeout_use_case,
        )
        return RollCommandHandlerImpl(
            command_prefix=command_prefix,
            command_name=command_name,
            handle_roll_use_case=handle_roll_use_case,
            chat_moderation=chat_moderation_port,
            bot_name=bot_name,
        )

    def shop_uow_factory(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_provider: Provider[ShopItemRepository],
    ) -> ShopUnitOfWorkFactory:
        return SqlAlchemyShopUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_provider=economy_policy_provider,
            add_equipment_use_case=add_equipment_use_case,
            equipment_exists_use_case=equipment_exists_use_case,
            chat_use_case=chat_use_case,
            shop_item_repository_provider=shop_item_repository_provider,
        )

    def handle_shop_use_case(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_provider: Provider[ShopItemRepository],
    ) -> HandleShopUseCase:
        shop_uow_factory = self.shop_uow_factory(
            economy_policy_provider, add_equipment_use_case, equipment_exists_use_case, chat_use_case, shop_item_repository_provider
        )
        return HandleShopUseCase(shop_uow_factory)

    def shop_command_handler(
        self,
        command_prefix: str,
        command_shop_name: str,
        command_buy_name: str,
        economy_policy_provider: Provider[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_provider: Provider[ShopItemRepository],
        bot_name: str,
    ) -> CommandHandler:
        handle_shop_use_case = self.handle_shop_use_case(
            economy_policy_provider, add_equipment_use_case, equipment_exists_use_case, chat_use_case, shop_item_repository_provider
        )
        return ShopCommandHandlerImpl(
            command_prefix=command_prefix,
            command_shop_name=command_shop_name,
            command_buy_name=command_buy_name,
            handle_shop_use_case=handle_shop_use_case,
            bot_nick=bot_name,
        )

    def buy_command_handler(
        self,
        command_prefix: str,
        command_buy_name: str,
        economy_policy_provider: Provider[EconomyPolicy],
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        shop_item_repository_provider: Provider[ShopItemRepository],
        bot_name: str,
    ) -> CommandHandler:
        handle_shop_use_case = self.handle_shop_use_case(
            economy_policy_provider, add_equipment_use_case, equipment_exists_use_case, chat_use_case, shop_item_repository_provider
        )
        return BuyCommandHandlerImpl(
            command_prefix=command_prefix, command_buy_name=command_buy_name, handle_shop_use_case=handle_shop_use_case, bot_nick=bot_name
        )
