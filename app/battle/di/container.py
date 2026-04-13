from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.uow.battle_use_case_uow import BattleUseCaseUnitOfWorkFactory
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.battle.domain.repo import BattleRepository
from app.battle.infrastructure.battle_repository import BattleRepositoryImpl
from app.battle.infrastructure.battle_use_case_uow import SqlAlchemyBattleUseCaseUnitOfWorkFactory
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.platform.command.battle.application.battle_uow import BattleUnitOfWorkFactory
from app.platform.command.battle.infrastructure.battle_uow import SqlAlchemyBattleUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class BattleContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._battle_repository_provider = Provider(self.battle_repository)

    def battle_repository(self, session: Session) -> BattleRepository:
        return BattleRepositoryImpl(session)

    def battle_use_case_uow_factory(self) -> BattleUseCaseUnitOfWorkFactory:
        return SqlAlchemyBattleUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            battle_repo_provider=self._battle_repository_provider,
        )

    def battle_use_case(self) -> BattleUseCase:
        battle_use_case_uow_factory = self.battle_use_case_uow_factory()
        return BattleUseCase(battle_use_case_uow_factory)

    def battle_uow_factory(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case: ChatUseCase,
        conversation_service_provider: Provider[ConversationService],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
    ) -> BattleUnitOfWorkFactory:
        return SqlAlchemyBattleUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_provider=economy_policy_provider,
            chat_use_case=chat_use_case,
            conversation_service_provider=conversation_service_provider,
            battle_use_case=self.battle_use_case(),
            get_user_equipment_use_case=get_user_equipment_use_case,
        )
