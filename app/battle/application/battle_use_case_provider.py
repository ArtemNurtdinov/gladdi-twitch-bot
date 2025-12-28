from typing import Callable

from sqlalchemy.orm import Session

from app.battle.application.battle_use_case import BattleUseCase
from app.chat.application.chat_use_case import ChatUseCase


class BattleUseCaseProvider:

    def __init__(self, battle_use_case_factory: Callable[[Session], BattleUseCase]):
        self._battle_use_case_factory = battle_use_case_factory

    def get(self, db: Session) -> BattleUseCase:
        return self._battle_use_case_factory(db)