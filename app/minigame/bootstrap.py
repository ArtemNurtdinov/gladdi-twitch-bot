from dataclasses import dataclass

from app.minigame.application.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.data.word_history_repository import WordHistoryRepositoryImpl
from app.minigame.domain.minigame_service import MinigameService
from core.provider import Provider


@dataclass
class MinigameProviders:
    minigame_service: MinigameService
    get_used_words_use_case_provider: Provider[GetUsedWordsUseCase]
    add_used_words_use_case_provider: Provider[AddUsedWordsUseCase]


def build_minigame_providers() -> MinigameProviders:
    minigame_service = MinigameService()

    def get_used_words_use_case(db):
        return GetUsedWordsUseCase(WordHistoryRepositoryImpl(db))

    def add_used_word_use_case(db):
        return AddUsedWordsUseCase(WordHistoryRepositoryImpl(db))

    return MinigameProviders(
        minigame_service=minigame_service,
        get_used_words_use_case_provider=Provider(get_used_words_use_case),
        add_used_words_use_case_provider=Provider(add_used_word_use_case),
    )
