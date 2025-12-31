from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.stream.application.stream_info_port import StreamInfoPort
from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.application.stream_status_port import StreamStatusPort
from app.stream.domain.repo import StreamRepository
from app.stream.domain.stream_service import StreamService
from app.stream.infrastructure.stream_chatters_adapter import StreamChattersAdapter
from app.stream.infrastructure.stream_info_adapter import StreamInfoAdapter
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from app.stream.infrastructure.stream_status_adapter import StreamStatusAdapter
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.viewer.application.stream_chatters_port import StreamChattersPort
from core.db import get_db_ro, get_db_rw
from core.provider import Provider


def get_stream_repo_ro(db: Session = Depends(get_db_ro)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_repo_rw(db: Session = Depends(get_db_rw)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_service_ro(repo: StreamRepositoryImpl = Depends(get_stream_repo_ro)) -> StreamService:
    return StreamService(repo)


def get_stream_service_rw(repo: StreamRepositoryImpl = Depends(get_stream_repo_rw)) -> StreamService:
    return StreamService(repo)


@dataclass
class StreamProviders:
    stream_info_port: StreamInfoPort
    stream_status_port: StreamStatusPort
    stream_chatters_port: StreamChattersPort
    stream_service_provider: Provider[StreamService]
    start_stream_use_case_provider: Provider[StartNewStreamUseCase]


def build_stream_providers(twitch_api_service: TwitchApiService) -> StreamProviders:

    def stream_service(db):
        return StreamService(StreamRepositoryImpl(db))

    def start_stream_use_case(db):
        return StartNewStreamUseCase(StreamRepositoryImpl(db))

    return StreamProviders(
        stream_info_port=StreamInfoAdapter(twitch_api_service),
        stream_status_port=StreamStatusAdapter(twitch_api_service),
        stream_chatters_port=StreamChattersAdapter(twitch_api_service),
        stream_service_provider=Provider(stream_service),
        start_stream_use_case_provider=Provider(start_stream_use_case),
    )
