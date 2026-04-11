from typing import Protocol

from app.viewer.application.model.viewer_detail_models import ViewerDetailInfo


class ViewerDetailInfoPort(Protocol):
    def get(self, channel_name: str, user_name: str) -> ViewerDetailInfo: ...
