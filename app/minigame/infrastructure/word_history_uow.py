from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.minigame.application.word_history_uow import WordHistoryUnitOfWork, WordHistoryUnitOfWorkFactory
from app.minigame.domain.repo import WordHistoryRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyWordHistoryUnitOfWork(SqlAlchemyUnitOfWorkBase, WordHistoryUnitOfWork):
    def __init__(self, session: Session, word_history_repo: WordHistoryRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._word_history_repo = word_history_repo

    @property
    def word_history_repo(self) -> WordHistoryRepository:
        return self._word_history_repo


class SqlAlchemyWordHistoryUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[WordHistoryUnitOfWork], WordHistoryUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        word_history_repo_provider: Provider[WordHistoryRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._word_history_repo_provider = word_history_repo_provider

    def _build_uow(self, db: Session, read_only: bool) -> WordHistoryUnitOfWork:
        return SqlAlchemyWordHistoryUnitOfWork(
            session=db,
            word_history_repo=self._word_history_repo_provider.get(db),
            read_only=read_only,
        )
