from typing import Callable

from sqlalchemy.orm import Session

from app.minigame.application.add_used_word_use_case import AddUsedWordsUseCase


class AddUsedWordsUseCaseProvider:

    def __init__(self, add_used_words_use_case_factory: Callable[[Session], AddUsedWordsUseCase]):
        self._add_used_words_use_case_factory = add_used_words_use_case_factory

    def get(self, db: Session) -> AddUsedWordsUseCase:
        return self._add_used_words_use_case_factory(db)
