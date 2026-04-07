from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWork, BonusUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from core.types import SessionFactory


class SqlAlchemyBonusUnitOfWork(SqlAlchemyUnitOfWorkBase, BonusUnitOfWork):
    def __init__(
        self,
        session: Session,
        stream_repository: StreamRepository,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy: EconomyPolicy,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._stream_repository = stream_repository
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case

    @property
    def stream_repository(self) -> StreamRepository:
        return self._stream_repository

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        return self._get_user_equipment_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyBonusUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[BonusUnitOfWork], BonusUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_repository_factory = stream_repository_factory
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._economy_policy_factory = economy_policy_factory
        self._chat_use_case = chat_use_case

    def _build_uow(self, db: Session, read_only: bool) -> BonusUnitOfWork:
        return SqlAlchemyBonusUnitOfWork(
            session=db,
            stream_repository=self._stream_repository_factory.get(db),
            get_user_equipment_use_case=self._get_user_equipment_use_case,
            economy_policy=self._economy_policy_factory.get(db),
            chat_use_case=self._chat_use_case,
            read_only=read_only,
        )
