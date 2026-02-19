from datetime import datetime
from typing import Protocol


class StreamChatStatsPort(Protocol):
    """Порт для получения статистики чата по стриму (по диапазону дат)."""

    def count_messages(self, channel_name: str, start: datetime, end: datetime) -> int: ...
