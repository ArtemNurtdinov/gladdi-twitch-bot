from dataclasses import dataclass, field
from typing import Optional, List

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class BattleDTO(ChatContextDTO):
    command_call: str
    waiting_user: Optional[str] = field(default=None)


@dataclass(frozen=True)
class BattleTimeoutAction:
    user_name: str
    duration_seconds: int
    reason: str


@dataclass(frozen=True)
class BattleUseCaseResult:
    messages: List[str]
    new_waiting_user: Optional[str]
    timeout_action: Optional[BattleTimeoutAction]
    delay_before_timeout: float = 0.0
