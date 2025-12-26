from typing import Callable

from sqlalchemy.orm import Session

from app.minigame.application.get_used_words_use_case import GetUsedWordsUseCase


class GetUsedWordsUseCaseProvider:

    def __init__(self, get_used_words_use_case_factory: Callable[[Session], GetUsedWordsUseCase]):
        self._get_used_words_use_case_factory = get_used_words_use_case_factory

    def get(self, db: Session) -> GetUsedWordsUseCase:
        return self._get_used_words_use_case_factory(db)
