from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
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
