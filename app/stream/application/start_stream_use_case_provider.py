from typing import Callable

from sqlalchemy.orm import Session

from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase


class StartStreamUseCaseProvider:

    def __init__(self, start_stream_use_case_factory: Callable[[Session], StartNewStreamUseCase]):
        self._start_stream_use_case_factory = start_stream_use_case_factory

    def get(self, db: Session) -> StartNewStreamUseCase:
        return self._start_stream_use_case_factory(db)
