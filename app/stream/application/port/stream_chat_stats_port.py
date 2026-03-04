from datetime import datetime
from typing import Protocol


class StreamChatStatsPort(Protocol):
    def count_messages(self, channel_name: str, start: datetime, end: datetime) -> int: ...
