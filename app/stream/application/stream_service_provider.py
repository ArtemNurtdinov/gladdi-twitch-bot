from typing import Callable

from sqlalchemy.orm import Session

from app.stream.domain.stream_service import StreamService


class StreamServiceProvider:

    def __init__(self, stream_service_factory: Callable[[Session], StreamService]):
        self._stream_service_factory = stream_service_factory

    def get(self, db: Session) -> StreamService:
        return self._stream_service_factory(db)


