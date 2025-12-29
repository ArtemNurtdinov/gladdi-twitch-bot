from typing import Callable

from app.equipment.application.defence.roll_cooldown_use_case import RollCooldownUseCase


class RollCooldownUseCaseProvider:

    def __init__(self, roll_cooldown_use_case: Callable[[], RollCooldownUseCase]):
        self._roll_cooldown_use_case = roll_cooldown_use_case

    def get(self) -> RollCooldownUseCase:
        return self._roll_cooldown_use_case()
