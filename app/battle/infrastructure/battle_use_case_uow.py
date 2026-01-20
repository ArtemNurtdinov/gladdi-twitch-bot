from __future__ import annotations

from sqlalchemy.orm import Session

from app.battle.application.battle_use_case_uow import BattleUseCaseUnitOfWork, BattleUseCaseUnitOfWorkFactory
from app.battle.domain.repo import BattleRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyBattleUseCaseUnitOfWork(SqlAlchemyUnitOfWorkBase, BattleUseCaseUnitOfWork):
    def __init__(self, session: Session, battle_repo: BattleRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._battle_repo = battle_repo

    @property
    def battle_repo(self) -> BattleRepository:
        return self._battle_repo


class SqlAlchemyBattleUseCaseUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[BattleUseCaseUnitOfWork], BattleUseCaseUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        battle_repo_provider: Provider[BattleRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._battle_repo_provider = battle_repo_provider

    def _build_uow(self, db: Session, read_only: bool) -> BattleUseCaseUnitOfWork:
        return SqlAlchemyBattleUseCaseUnitOfWork(
            session=db,
            battle_repo=self._battle_repo_provider.get(db),
            read_only=read_only,
        )
