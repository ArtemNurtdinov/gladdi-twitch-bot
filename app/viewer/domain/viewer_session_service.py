import logging
from typing import List
from datetime import datetime

from app.viewer.domain.models import ViewerSession
from app.viewer.domain.repo import ViewerRepository

logger = logging.getLogger(__name__)


class ViewerTimeService:
    STREAM_TIME_REWARDS = {
        30: 25,
        60: 50,
        90: 100,
        120: 150,
        150: 250,
        180: 350
    }

    def __init__(self, repo: ViewerRepository):
        self._repo = repo

    def update_viewer_session(self, stream_id: int, channel_name: str, user_name: str, current_time: datetime):
        session = self._repo.get_viewer_session(stream_id, channel_name, user_name)
        if session:
            self._repo.update_last_activity(stream_id, channel_name, user_name, current_time)
        else:
            self._repo.create_view_session(stream_id, channel_name, user_name, current_time)

    def update_viewers(self, active_stream_id: int, channel_name: str, chatters: list[str], current_time: datetime):
        for user_name in chatters:
            normalized_user_name = user_name.lower()
            session = self._repo.get_viewer_session(active_stream_id, channel_name, normalized_user_name)
            if session:
                self._repo.update_last_activity(active_stream_id, channel_name, user_name, current_time)
            else:
                self._repo.create_view_session(active_stream_id, channel_name, user_name, current_time)

    def check_inactive_viewers(self, active_stream_id: int, current_time: datetime) -> list[str]:
        inactive_users = []
        inactive_sessions = self._repo.get_inactive_sessions(active_stream_id, current_time)

        for session in inactive_sessions:
            inactive_users.append(session.user_name)
            session_duration = datetime.utcnow() - session.session_start
            session_minutes = int(session_duration.total_seconds() / 60)
            total_minutes = session.total_minutes + session_minutes
            self._repo.finish_session(active_stream_id, session.channel_name, session.user_name, total_minutes, current_time)
        return inactive_users

    def get_stream_viewer_sessions(self, stream_id: int) -> list[ViewerSession]:
        return self._repo.get_viewer_sessions(stream_id)

    def get_user_sessions(self, channel_name: str, user_name: str) -> List[ViewerSession]:
        return self._repo.get_user_sessions(channel_name, user_name)

    def get_available_rewards(self, session: ViewerSession) -> list[tuple]:
        available_rewards = []

        if session.is_watching and session.session_start:
            duration = datetime.utcnow() - session.session_start
            current_session_minutes = int(duration.total_seconds() / 60)
        else:
            current_session_minutes = 0

        total_minutes = session.total_minutes + current_session_minutes
        claimed_rewards = set(session.get_claimed_rewards_list())

        for minutes_threshold in sorted(self.STREAM_TIME_REWARDS.keys()):
            if total_minutes >= minutes_threshold and minutes_threshold not in claimed_rewards:
                reward_amount = self.STREAM_TIME_REWARDS[minutes_threshold]
                available_rewards.append((minutes_threshold, reward_amount))

        return available_rewards

    def get_stream_watchers_count(self, stream_id: int) -> int:
        return self._repo.get_stream_watchers_count(stream_id)

    def finish_stream_sessions(self, stream_id: int, current_time: datetime):
        active_sessions = self._repo.get_active_sessions(stream_id)

        for session in active_sessions:
            session_duration = current_time - session.session_start
            session_minutes = int(session_duration.total_seconds() / 60)
            total_minutes = session.total_minutes + session_minutes
            self._repo.finish_session(stream_id, session.channel_name, session.user_name, total_minutes, current_time)

    def get_unique_viewers_count(self, stream_id: int) -> int:
        return self._repo.get_unique_viewers_count(stream_id)

    def update_session_rewards(self, session_id: int, rewards: str, current_time: datetime):
        self._repo.update_session_rewards(session_id, rewards, current_time)
