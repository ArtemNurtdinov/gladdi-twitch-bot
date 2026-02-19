from datetime import datetime

from app.chat.domain.repo import ChatRepository
from app.stream.application.stream_chat_stats_port import StreamChatStatsPort


class StreamChatStatsAdapter(StreamChatStatsPort):
    def __init__(self, chat_repo: ChatRepository):
        self._chat_repo = chat_repo

    def count_messages(self, channel_name: str, start: datetime, end: datetime) -> int:
        return self._chat_repo.count_between(channel_name, start, end)
