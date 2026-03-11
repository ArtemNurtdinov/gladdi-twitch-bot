from dataclasses import dataclass

from app.minigame.application.use_case.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.use_case.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.infrastructure.minigame_repository import MinigameRepositoryImpl
from app.minigame.infrastructure.uow.word_history_uow import SqlAlchemyWordHistoryUnitOfWorkFactory
from app.minigame.infrastructure.word_history_repository import WordHistoryRepositoryImpl
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


@dataclass
class MinigameProviders:
    minigame_repository: MinigameRepository
    get_used_words_use_case_provider: Provider[GetUsedWordsUseCase]
    add_used_words_use_case_provider: Provider[AddUsedWordsUseCase]


def build_minigame_providers() -> MinigameProviders:
    minigame_repository = MinigameRepositoryImpl()

    def word_history_repo(db):
        return WordHistoryRepositoryImpl(db)

    def get_used_words_use_case(db):
        return GetUsedWordsUseCase(
            unit_of_work_factory=SqlAlchemyWordHistoryUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                word_history_repo_provider=Provider(word_history_repo),
            )
        )

    def add_used_word_use_case(db):
        return AddUsedWordsUseCase(
            unit_of_work_factory=SqlAlchemyWordHistoryUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                word_history_repo_provider=Provider(word_history_repo),
            )
        )

    return MinigameProviders(
        minigame_repository=minigame_repository,
        get_used_words_use_case_provider=Provider(get_used_words_use_case),
        add_used_words_use_case_provider=Provider(add_used_word_use_case),
    )
