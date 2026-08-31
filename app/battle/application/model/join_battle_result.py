from dataclasses import dataclass


@dataclass(frozen=True)
class JoinBattleResult:
    messages: list[str]
    matched_opponent: str | None
