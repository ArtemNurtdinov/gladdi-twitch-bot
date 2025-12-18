from dataclasses import dataclass
from typing import List

from features.stream.domain.models import StreamInfo, StreamViewerSessionInfo


@dataclass
class StreamDetail:
    stream: StreamInfo
    sessions: List[StreamViewerSessionInfo]
