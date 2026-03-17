from dataclasses import dataclass

from app.stream.application.usecase.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.domain.stream_service import StreamService
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from app.stream.infrastructure.uow.start_new_stream_uow import SqlAlchemyStartNewStreamUnitOfWorkFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


@dataclass
class StreamProviders:
    stream_service_provider: Provider[StreamService]
    start_stream_use_case_provider: Provider[StartNewStreamUseCase]
    stream_repo_provider: Provider[StreamRepository]


def build_stream_providers() -> StreamProviders:
    def stream_repo(db):
        return StreamRepositoryImpl(db)

    def stream_service(db):
        return StreamService(StreamRepositoryImpl(db))

    def start_stream_use_case(db):
        return StartNewStreamUseCase(
            unit_of_work_factory=SqlAlchemyStartNewStreamUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                stream_repo_provider=Provider(stream_repo),
            )
        )

    return StreamProviders(
        stream_service_provider=Provider(stream_service),
        start_stream_use_case_provider=Provider(start_stream_use_case),
        stream_repo_provider=Provider(stream_repo),
    )
