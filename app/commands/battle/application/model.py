from dataclasses import dataclass, field

from app.commands.dto import ChatContextDTO


@dataclass(frozen=True)
class BattleDTO(ChatContextDTO):
    command_call: str
    waiting_user: str | None = field(default=None)


@dataclass(frozen=True)
class BattleTimeoutAction:
    user_name: str
    duration_seconds: int
    reason: str


@dataclass(frozen=True)
class BattleUseCaseResult:
    messages: list[str]
    new_waiting_user: str | None
    timeout_action: BattleTimeoutAction | None
    delay_before_timeout: float = 0.0
