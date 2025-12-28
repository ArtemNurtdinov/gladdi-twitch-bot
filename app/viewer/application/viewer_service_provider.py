from typing import Callable

from sqlalchemy.orm import Session

from app.viewer.domain.viewer_session_service import ViewerTimeService


class ViewerServiceProvider:

    def __init__(self, viewer_service_factory: Callable[[Session], ViewerTimeService]):
        self._viewer_service_factory = viewer_service_factory

    def get(self, db: Session) -> ViewerTimeService:
        return self._viewer_service_factory(db)
