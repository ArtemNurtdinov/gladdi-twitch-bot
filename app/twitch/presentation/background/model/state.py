from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatSummaryState:
    current_stream_summaries: list[str] = field(default_factory=list)
    last_chat_summary_time: datetime | None = None
