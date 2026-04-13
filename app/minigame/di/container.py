from sqlalchemy.orm import Session

from app.core.logger.domain.logger import Logger
from app.minigame.application.uow.word_history_uow import WordHistoryUnitOfWorkFactory
from app.minigame.application.use_case.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.use_case.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.domain.word_history_repository import WordHistoryRepository
from app.minigame.infrastructure.minigame_repository import MinigameRepositoryImpl
from app.minigame.infrastructure.uow.word_history_uow import SqlAlchemyWordHistoryUnitOfWorkFactory
from app.minigame.infrastructure.word_history_repository import WordHistoryRepositoryImpl
from core.provider import Provider
from core.types import SessionFactory


class MinigameContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory, logger: Logger):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._word_history_repo_provider = Provider(self.word_history_repository)
        self._logger = logger.create_child(__name__)

    def minigame_repository(self) -> MinigameRepository:
        return MinigameRepositoryImpl(self._logger)

    def word_history_repository(self, session: Session) -> WordHistoryRepository:
        return WordHistoryRepositoryImpl(session)

    def word_history_uow_factory(self) -> WordHistoryUnitOfWorkFactory:
        return SqlAlchemyWordHistoryUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            word_history_repo_provider=self._word_history_repo_provider,
        )

    def get_used_words_use_case(self) -> GetUsedWordsUseCase:
        word_history_uow_factory = self.word_history_uow_factory()
        return GetUsedWordsUseCase(word_history_uow_factory)

    def add_used_word_use_case(self) -> AddUsedWordsUseCase:
        word_history_uow_factory = self.word_history_uow_factory()
        return AddUsedWordsUseCase(word_history_uow_factory)
