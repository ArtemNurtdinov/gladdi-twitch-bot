from datetime import datetime
from typing import Generic, Optional, Protocol, TypeVar

from features.viewer.domain.models import ViewerSession

DB = TypeVar("DB")

class ViewerRepository(Protocol, Generic[DB]):

    def get_viewer_session(self, db: DB, stream_id: int, channel_name: str, user_name: str) -> Optional[ViewerSession]:
        ...

    def create_view_session(self, db: DB, stream_id: int, channel_name: str, user_name: str, current_time: datetime) -> ViewerSession:
        ...

    def update_last_activity(self, db: DB, stream_id: int, channel_name: str, user_name: str, current_time: datetime):
        ...

    def get_inactive_sessions(self, db: DB, stream_id: int, current_time: datetime) -> list[ViewerSession]:
        ...

    def finish_session(
        self,
        db: DB,
        stream_id: int,
        channel_name: str,
        user_name: str,
        total_minutes: int,
        current_time: datetime
    ):
        ...

    def get_active_sessions(self, db: DB, stream_id: int) -> list[ViewerSession]:
        ...

    def get_unique_viewers_count(self, db: DB, stream_id: int) -> int:
        ...

    def get_viewer_sessions(self, db: DB, stream_id: int) -> list[ViewerSession]:
        ...

    def update_session_rewards(self, db: DB, session_id: int, rewards: str, current_time: datetime):
        ...

    def get_user_sessions(self, db: DB, channel_name: str, user_name: str) -> list[ViewerSession]:
        ...

    def get_stream_watchers_count(self, db: DB, stream_id: int) -> int:
        ...