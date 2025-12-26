import logging
import httpx
from typing import Optional, Dict, Any, List
from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.model.stream_info import StreamInfo
from app.twitch.infrastructure.model.user_info import UserInfo
from app.twitch.infrastructure.model.follow_info import FollowInfo
from app.twitch.infrastructure.model.stream_status import StreamStatus, StreamData
from app.twitch.infrastructure.model.channel_info import ChannelInfo

logger = logging.getLogger(__name__)


class TwitchApiService:

    def __init__(self, twitch_auth: TwitchAuth):
        self.twitch_auth = twitch_auth
        self.base_url = 'https://api.twitch.tv/helix'
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Client-ID': self.twitch_auth.client_id,
            'Authorization': f'Bearer {self.twitch_auth.access_token}'
        }

    async def _handle_api_response(self, response: httpx.Response, operation: str) -> Dict[str, Any]:
        if response.status_code == 200:
            logger.debug(f"API операция '{operation}' выполнена успешно")
            return response.json()
        else:
            logger.error(f"Ошибка в API операции '{operation}': {response.status_code}, {response.text}")
            raise Exception(f"API операция '{operation}' завершилась с ошибкой: {response.status_code}")

    async def get_user_by_login(self, login: str) -> Optional[UserInfo]:
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

            data = response.json()
            if not data.get('data'):
                logger.warning(f"Пользователь {login} не найден в ответе API")
                return None

            user_data = data['data'][0]
            logger.debug(f"Информация о пользователе {login} получена")

            return UserInfo(
                id=user_data['id'],
                login=user_data['login'],
                display_name=user_data['display_name'],
                type=user_data.get('type', ''),
                broadcaster_type=user_data.get('broadcaster_type', ''),
                description=user_data.get('description', ''),
                profile_image_url=user_data.get('profile_image_url', ''),
                offline_image_url=user_data.get('offline_image_url', ''),
                view_count=user_data.get('view_count', 0),
                email=user_data.get('email'),
                created_at=user_data.get('created_at')
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

    async def get_user_followage(self, broadcaster_id: str, user_id: str) -> Optional[FollowInfo]:
        logger.debug(f"Получение информации о подписке пользователя {user_id} на канал {broadcaster_id}")

        url = '/channels/followers'
        headers = self._get_headers()
        params = {
            'broadcaster_id': broadcaster_id,
            'user_id': user_id
        }

        response = await self._client.get(url, headers=headers, params=params)
        data = await self._handle_api_response(response, f"get_user_followage({broadcaster_id}, {user_id})")

        if data['data']:
            follow_data = data['data'][0]
            logger.debug(f"Пользователь {user_id} подписан с {follow_data['followed_at']}")
            return FollowInfo( follow_data['user_id'], follow_data['user_name'], follow_data['user_login'],follow_data['followed_at'])
        else:
            logger.debug(f"Пользователь {user_id} не подписан на канал {broadcaster_id}")
            return None

    async def get_stream_info(self, broadcaster_id: str) -> StreamInfo:
        channel_info = await self.get_channel_info(broadcaster_id)
        return StreamInfo(channel_info.game_name, channel_info.title)

    async def get_stream_status(self, broadcaster_id: str) -> Optional[StreamStatus]:
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

            data = response.json()
            if data.get('data'):
                stream_raw = data['data'][0]
                stream_data = StreamData(
                    id=stream_raw['id'],
                    user_id=stream_raw['user_id'],
                    user_login=stream_raw['user_login'],
                    user_name=stream_raw['user_name'],
                    game_id=stream_raw['game_id'],
                    game_name=stream_raw['game_name'],
                    type=stream_raw['type'],
                    title=stream_raw['title'],
                    viewer_count=stream_raw['viewer_count'],
                    started_at=stream_raw['started_at'],
                    language=stream_raw['language'],
                    thumbnail_url=stream_raw['thumbnail_url'],
                    tag_ids=stream_raw.get('tag_ids', []),
                    is_mature=stream_raw.get('is_mature', False)
                )
                logger.debug(f"Стрим для {broadcaster_id}: онлайн")
                return StreamStatus(is_online=True, stream_data=stream_data)
            else:
                logger.debug(f"Стрим для {broadcaster_id}: офлайн")
                return StreamStatus(is_online=False, stream_data=None)
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

    async def get_channel_info(self, broadcaster_id: str) -> ChannelInfo:
        logger.debug(f"Получение информации о канале: {broadcaster_id}")

        url = '/channels'
        headers = self._get_headers()
        params = {'broadcaster_id': broadcaster_id}

        response = await self._client.get(url, headers=headers, params=params)
        data = await self._handle_api_response(response, f"get_channel_info({broadcaster_id})")

        if not data['data']:
            logger.error(f"Не удалось получить информацию о канале {broadcaster_id}")
            raise Exception('Не удалось получить информацию о канале')

        channel_data = data['data'][0]
        return ChannelInfo(
            broadcaster_id=channel_data['broadcaster_id'],
            broadcaster_login=channel_data['broadcaster_login'],
            broadcaster_name=channel_data['broadcaster_name'],
            broadcaster_language=channel_data.get('broadcaster_language', ''),
            game_id=channel_data.get('game_id', ''),
            game_name=channel_data.get('game_name', ''),
            title=channel_data.get('title', ''),
            delay=channel_data.get('delay', 0),
            tags=channel_data.get('tags', []),
            content_classification_labels=channel_data.get('content_classification_labels'),
            is_branded_content=channel_data.get('is_branded_content', False)
        )

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

            chatters = []
            if 'data' in data:
                for chatter in data['data']:
                    if 'user_login' in chatter:
                        chatters.append(chatter['user_login'])
            return chatters
        except Exception as e:
            logger.error(f"Ошибка при получении списка зрителей: {e}")
            return []
