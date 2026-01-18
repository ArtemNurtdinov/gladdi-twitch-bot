from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.battle_use_case import BattleUseCase
from app.chat.application.chat_use_case import ChatUseCase
from app.commands.battle.application.battle_uow import BattleUnitOfWork, BattleUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyBattleUnitOfWork(SqlAlchemyUnitOfWorkBase, BattleUnitOfWork):
    def __init__(
        self,
        session: Session,
        economy_policy: EconomyPolicy,
        chat_use_case: ChatUseCase,
        conversation_service: ConversationService,
        battle_use_case: BattleUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case
        self._conversation_service = conversation_service
        self._battle_use_case = battle_use_case
        self._get_user_equipment_use_case = get_user_equipment_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def battle_use_case(self) -> BattleUseCase:
        return self._battle_use_case

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        return self._get_user_equipment_use_case


class SqlAlchemyBattleUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[BattleUnitOfWork], BattleUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case_provider: Provider[ChatUseCase],
        conversation_service_provider: Provider[ConversationService],
        battle_use_case_provider: Provider[BattleUseCase],
        get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider
        self._battle_use_case_provider = battle_use_case_provider
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> BattleUnitOfWork:
        return SqlAlchemyBattleUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            conversation_service=self._conversation_service_provider.get(db),
            battle_use_case=self._battle_use_case_provider.get(db),
            get_user_equipment_use_case=self._get_user_equipment_use_case_provider.get(db),
            read_only=read_only,
        )
