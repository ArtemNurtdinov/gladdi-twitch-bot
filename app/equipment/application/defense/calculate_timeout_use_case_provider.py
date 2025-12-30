from typing import Callable

from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase


class CalculateTimeoutUseCaseProvider:

    def __init__(self, calculate_timeout_use_case: Callable[[], CalculateTimeoutUseCase]):
        self._calculate_timeout_use_case = calculate_timeout_use_case

    def get(self) -> CalculateTimeoutUseCase:
        return self._calculate_timeout_use_case()
