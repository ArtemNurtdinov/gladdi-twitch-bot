from __future__ import annotations

import logging

import httpx
from pydantic import ValidationError

from app.stream.application.model import StreamDataDTO, StreamStatusDTO
from app.stream.application.stream_info_port import StreamInfoPort
from app.stream.application.stream_status_port import StreamStatusPort
from app.twitch.infrastructure.adapters.user_info_adapter import UserInfoApiAdapter
from core.platform.api_client import StreamingApiClient
from app.twitch.infrastructure.twitch_api_models import StreamsResponse

logger = logging.getLogger(__name__)


class StreamApiAdapter(StreamInfoPort, StreamStatusPort):
    def __init__(self, client: StreamingApiClient, user_info: UserInfoApiAdapter):
        self._client = client
        self._user_info = user_info

    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None:
        try:
            response = await self._client.get("/streams", params={"user_id": broadcaster_id})
            if response.status_code == 401:
                logger.error(f"Ошибка авторизации при получении статуса стрима {broadcaster_id}. Проверьте токен.")
                return None
            if response.status_code != 200:
                logger.error(f"API ошибка при получении статуса стрима {broadcaster_id}: {response.status_code}, {response.text}")
                return None

            try:
                parsed = StreamsResponse.model_validate(response.json())
            except ValidationError as e:
                logger.error(f"Валидация статуса стрима {broadcaster_id} не прошла: {e}")
                return None

            streams = parsed.data
            if streams:
                stream_raw = streams[0]
                started_at = stream_raw.started_at.replace(tzinfo=None) if stream_raw.started_at else None
                stream_data = StreamDataDTO(
                    id=stream_raw.id,
                    user_id=stream_raw.user_id,
                    user_login=stream_raw.user_login,
                    user_name=stream_raw.user_name,
                    game_id=stream_raw.game_id,
                    game_name=stream_raw.game_name,
                    type=stream_raw.type,
                    title=stream_raw.title,
                    viewer_count=stream_raw.viewer_count,
                    started_at=started_at,
                    language=stream_raw.language,
                    thumbnail_url=stream_raw.thumbnail_url,
                    tag_ids=stream_raw.tag_ids,
                    is_mature=stream_raw.is_mature,
                )
                logger.debug(f"Стрим для {broadcaster_id}: онлайн")
                return StreamStatusDTO(is_online=True, stream_data=stream_data)
            logger.debug(f"Стрим для {broadcaster_id}: офлайн")
            return StreamStatusDTO(is_online=False, stream_data=None)
        except httpx.TimeoutException:
            logger.error(f"Таймаут при получении статуса стрима {broadcaster_id}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения при получении статуса стрима {broadcaster_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении статуса стрима {broadcaster_id}: {e}")
            return None

    async def get_stream_info(self, channel_name: str) -> StreamDataDTO | None:
        user = await self._user_info.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return None
        status = await self.get_stream_status(broadcaster_id)
        if not status or not status.is_online or not status.stream_data:
            return None
        return status.stream_data
