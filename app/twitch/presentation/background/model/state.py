from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ChatSummaryState:
    current_stream_summaries: List[str] = field(default_factory=list)
    last_chat_summary_time: Optional[datetime] = None

