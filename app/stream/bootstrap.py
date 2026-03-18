from dataclasses import dataclass

from app.stream.domain.repo import StreamRepository
from app.stream.domain.stream_service import StreamService
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from core.provider import Provider


@dataclass
class StreamProviders:
    stream_service_provider: Provider[StreamService]
    stream_repo_provider: Provider[StreamRepository]


def build_stream_providers() -> StreamProviders:
    def stream_repo(db):
        return StreamRepositoryImpl(db)

    def stream_service(db):
        return StreamService(StreamRepositoryImpl(db))

    return StreamProviders(
        stream_service_provider=Provider(stream_service),
        stream_repo_provider=Provider(stream_repo),
    )
