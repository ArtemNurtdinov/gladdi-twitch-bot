from __future__ import annotations

import logging
import httpx
from typing import Optional, Dict, Any, List

from pydantic import ValidationError

from app.follow.application.model import ChannelFollowerDTO
from app.twitch.application.common.model import StreamStatusDTO, StreamDataDTO, UserInfoDTO
from app.twitch.application.interaction.follow.followage_port import FollowagePort
from app.twitch.application.interaction.follow.model import FollowageInfo
from app.twitch.application.common.stream_info_port import StreamInfoPort
from app.twitch.application.common.stream_status_port import StreamStatusPort
from app.twitch.application.common.user_info_port import UserInfoPort
from app.twitch.application.common.stream_chatters_port import StreamChattersPort
from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.twitch_api_models import (
    UsersResponse,
    StreamsResponse,
    FollowersResponse,
    ChattersResponse,
    FollowerData,
)

logger = logging.getLogger(__name__)


class TwitchApiService(
    FollowagePort,
    StreamInfoPort,
    StreamStatusPort,
    UserInfoPort,
    StreamChattersPort,
):

    def __init__(self, twitch_auth: TwitchAuth):
        self._twitch_auth = twitch_auth
        self._base_url = 'https://api.twitch.tv/helix'
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Client-ID': self._twitch_auth.client_id,
            'Authorization': f'Bearer {self._twitch_auth.access_token}'
        }

    async def _handle_api_response(self, response: httpx.Response, operation: str) -> Dict[str, Any]:
        if response.status_code == 200:
            logger.debug(f"API операция '{operation}' выполнена успешно")
            return response.json()
        else:
            logger.error(f"Ошибка в API операции '{operation}': {response.status_code}, {response.text}")
            raise Exception(f"API операция '{operation}' завершилась с ошибкой: {response.status_code}")

    async def get_user_by_login(self, login: str) -> Optional[UserInfoDTO]:
        logger.debug(f"Получение информации о пользователе для логина: {login}")

        url = '/users'
        headers = self._get_headers()
        params = {'login': login}

        try:
            response = await self._client.get(url, headers=headers, params=params)
            if response.status_code == 401:
                logger.error(f"Ошибка авторизации при получении пользователя {login}. Проверьте токен.")
                return None
            elif response.status_code == 404:
                logger.warning(f"Пользователь {login} не найден")
                return None
            elif response.status_code != 200:
                logger.error(f"API ошибка при получении пользователя {login}: {response.status_code}, {response.text}")
                return None

            try:
                parsed = UsersResponse.model_validate(response.json())
            except ValidationError as e:
                logger.error(f"Валидация пользователя {login} не прошла: {e}")
                return None

            if not parsed.data:
                logger.warning(f"Пользователь {login} не найден в ответе API")
                return None

            user_data = parsed.data[0]
            logger.debug(f"Информация о пользователе {login} получена")

            return UserInfoDTO(
                id=user_data.id,
                login=user_data.login,
                display_name=user_data.display_name,
            )
        except httpx.TimeoutException:
            logger.error(f"Таймаут при получении пользователя {login}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения при получении пользователя {login}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении пользователя {login}: {e}")
            return None

    async def _get_user_followage(self, broadcaster_id: str, user_id: str) -> Optional[FollowageInfo]:
        logger.debug(f"Получение информации о подписке пользователя {user_id} на канал {broadcaster_id}")

        url = '/channels/followers'
        headers = self._get_headers()
        params = {
            'broadcaster_id': broadcaster_id,
            'user_id': user_id
        }

        response = await self._client.get(url, headers=headers, params=params)
        try:
            data = await self._handle_api_response(response, f"get_user_followage({broadcaster_id}, {user_id})")
            parsed: FollowersResponse = FollowersResponse.model_validate(data)
        except ValidationError as e:
            logger.error(f"Валидация followage для {user_id} не прошла: {e}")
            return None

        followers: List[FollowerData] = parsed.data
        if followers:
            follow_data = followers[0]
            follow_dt = follow_data.followed_at.replace(tzinfo=None)
            logger.debug(f"Пользователь {user_id} подписан с {follow_data.followed_at}")
            return FollowageInfo(
                user_id=follow_data.user_id,
                user_name=follow_data.user_name,
                user_login=follow_data.user_login,
                followed_at=follow_dt,
            )
        logger.debug(f"Пользователь {user_id} не подписан на канал {broadcaster_id}")
        return None

    async def get_followage(self, channel_name: str, user_id: str) -> Optional[FollowageInfo]:
        user = await self.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return None

        return await self._get_user_followage(broadcaster_id=broadcaster_id, user_id=user_id)

    async def _get_channel_followers(self, broadcaster_id: str) -> List[ChannelFollowerDTO]:
        url = '/channels/followers'
        headers = self._get_headers()
        params = {'broadcaster_id': broadcaster_id, 'first': 100}
        followers: List[ChannelFollowerDTO] = []
        cursor = None

        while True:
            if cursor:
                params['after'] = cursor
            elif 'after' in params:
                params.pop('after')

            response = await self._client.get(url, headers=headers, params=params)
            try:
                data = await self._handle_api_response(response, f"get_channel_followers({broadcaster_id})")
                parsed: FollowersResponse = FollowersResponse.model_validate(data)
                followers_page: List[FollowerData] = parsed.data
            except ValidationError as e:
                logger.error(f"Валидация списка подписчиков {broadcaster_id} не прошла: {e}")
                break

            followers.extend([
                ChannelFollowerDTO(
                    user_id=item.user_id,
                    user_name=item.user_login,
                    display_name=item.user_name,
                    followed_at=item.followed_at.replace(tzinfo=None),
                )
                for item in followers_page
            ])

            pagination = data.get('pagination') if isinstance(data, dict) else None
            cursor = None if not pagination else pagination.get('cursor')
            if not cursor or not parsed.data:
                break

        return followers

    async def get_channel_followers(self, channel_name: str) -> List[ChannelFollowerDTO]:
        user = await self.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return []

        return await self._get_channel_followers(broadcaster_id=broadcaster_id)

    async def get_stream_info(self, channel_name: str) -> Optional[StreamDataDTO]:
        user = await self.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return None

        stream_status = await self.get_stream_status(broadcaster_id)
        if not stream_status or not stream_status.is_online or not stream_status.stream_data:
            return None

        return stream_status.stream_data

    async def get_stream_status(self, broadcaster_id: str) -> Optional[StreamStatusDTO]:
        url = '/streams'
        headers = self._get_headers()
        params = {'user_id': broadcaster_id}

        try:
            response = await self._client.get(url, headers=headers, params=params)
            if response.status_code == 401:
                logger.error(f"Ошибка авторизации при получении статуса стрима {broadcaster_id}. Проверьте токен.")
                return None
            elif response.status_code != 200:
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
            else:
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

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        logger.debug(f"Применение таймаута пользователю {user_id} на {duration_seconds} секунд")

        url = '/moderation/bans'
        headers = self._get_headers()
        headers['Content-Type'] = 'application/json'

        data = {
            "data": {
                "user_id": user_id,
                "duration": duration_seconds,
                "reason": reason
            }
        }

        params = {
            'broadcaster_id': broadcaster_id,
            'moderator_id': moderator_id
        }

        response = await self._client.post(url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            logger.info(f"Таймаут успешно применён для пользователя {user_id} на {duration_seconds} секунд за: {reason}")
            return True
        else:
            logger.error(f"Не удалось дать таймаут пользователю {user_id}. Status: {response.status_code}, Response: {response.text}")
            return False

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> List[str]:
        url = '/chat/chatters'
        headers = self._get_headers()
        params = {
            'broadcaster_id': broadcaster_id,
            'moderator_id': moderator_id
        }

        try:
            response = await self._client.get(url, headers=headers, params=params)
            data = await self._handle_api_response(response, f"get_stream_chatters({broadcaster_id})")
            try:
                parsed: ChattersResponse = ChattersResponse.model_validate(data)
            except ValidationError as e:
                logger.error(f"Валидация chatters для {broadcaster_id} не прошла: {e}")
                return []

            chatters = parsed.data
            return [ch.user_login for ch in chatters]
        except Exception as e:
            logger.error(f"Ошибка при получении списка зрителей: {e}")
            return []
