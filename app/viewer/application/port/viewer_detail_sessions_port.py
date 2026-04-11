from typing import Protocol

from app.viewer.application.model.viewer_detail_models import ViewerSessionDetail


class ViewerDetailSessionsPort(Protocol):
    def get_user_sessions(self, channel_name: str, user_name: str) -> list[ViewerSessionDetail]: ...
