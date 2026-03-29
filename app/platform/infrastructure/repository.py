import httpx
from pydantic import ValidationError

from app.core.logger.domain.logger import Logger
from app.follow.application.models.follower import ChannelFollowerDTO
from app.platform.command.followage.application.model import FollowageInfo
from app.platform.domain.repository import PlatformRepository
from app.platform.infrastructure.api_client import StreamingApiClient
from app.platform.infrastructure.common import handle_api_response
from app.platform.infrastructure.model.chatter import ChattersResponse
from app.platform.infrastructure.model.follower import FollowerData, FollowersResponse
from app.platform.infrastructure.model.stream import StreamsResponse
from app.platform.infrastructure.model.user import UsersResponse
from app.stream.application.models.stream_info import StreamInfoDTO
from app.stream.application.models.stream_status import StreamStatusDTO
from app.user.application.model.model import UserInfoDTO


class PlatformRepositoryImpl(PlatformRepository):
    def __init__(self, client: StreamingApiClient, logger: Logger):
        self._api_client = client
        self._logger = logger

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        response = await self._api_client.post(
            url="/moderation/bans",
            params={"broadcaster_id": broadcaster_id, "moderator_id": moderator_id},
            headers={"Content-Type": "application/json"},
            json={"data": {"user_id": user_id, "duration": duration_seconds, "reason": reason}},
        )
        if response.status_code == 200:
            self._logger.log_info(f"Таймаут успешно применён для пользователя {user_id} на {duration_seconds} секунд за: {reason}")
            return True
        else:
            self._logger.log_error(
                f"Не удалось дать таймаут пользователю {user_id}. Status: {response.status_code}, Response: {response.text}"
            )
            return False

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> list[str]:
        try:
            response = await self._api_client.get(
                url="/chat/chatters", params={"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
            )
            data = await handle_api_response(response, f"get_stream_chatters({broadcaster_id})")
            try:
                parsed: ChattersResponse = ChattersResponse.model_validate(data)
            except ValidationError as e:
                self._logger.log_error(f"Валидация chatters для {broadcaster_id} не прошла: {e}")
                return []

            chatters = parsed.data
            return [ch.user_login for ch in chatters]
        except Exception as e:
            self._logger.log_error(f"Ошибка при получении списка зрителей: {e}")
            return []

    async def get_user_by_login(self, login: str) -> UserInfoDTO | None:
        self._logger.log_debug(f"Получение информации о пользователе для логина: {login}")
        try:
            response = await self._api_client.get(url="/users", params={"login": login})
            if response.status_code == 401:
                self._logger.log_error(f"Ошибка авторизации при получении пользователя {login}. Проверьте токен.")
                return None
            if response.status_code == 404:
                self._logger.log_error(f"Пользователь {login} не найден")
                return None
            if response.status_code != 200:
                self._logger.log_error(f"API ошибка при получении пользователя {login}: {response.status_code}, {response.text}")
                return None

            try:
                parsed = UsersResponse.model_validate(response.json_data)
            except ValidationError as e:
                self._logger.log_error(f"Валидация пользователя {login} не прошла: {e}")
                return None

            if not parsed.data:
                self._logger.log_error(f"Пользователь {login} не найден в ответе API")
                return None

            user_data = parsed.data[0]
            self._logger.log_debug(f"Информация о пользователе {login} получена")
            return UserInfoDTO(id=user_data.id, login=user_data.login, display_name=user_data.display_name)
        except httpx.TimeoutException:
            self._logger.log_error(f"Таймаут при получении пользователя {login}")
            return None
        except httpx.RequestError as e:
            self._logger.log_error(f"Ошибка соединения при получении пользователя {login}: {e}")
            return None
        except Exception as e:
            self._logger.log_error(f"Неожиданная ошибка при получении пользователя {login}: {e}")
            return None

    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None:
        try:
            response = await self._api_client.get(url="/streams", params={"user_id": broadcaster_id})
            if response.status_code == 401:
                self._logger.log_error(f"Ошибка авторизации при получении статуса стрима {broadcaster_id}. Проверьте токен.")
                return None
            if response.status_code != 200:
                self._logger.log_error(f"API ошибка при получении статуса стрима {broadcaster_id}: {response.status_code}, {response.text}")
                return None

            try:
                parsed = StreamsResponse.model_validate(response.json_data)
            except ValidationError as e:
                self._logger.log_error(f"Валидация статуса стрима {broadcaster_id} не прошла: {e}")
                return None

            streams = parsed.data
            if streams:
                stream_raw = streams[0]
                started_at = stream_raw.started_at.replace(tzinfo=None) if stream_raw.started_at else None
                stream_data = StreamInfoDTO(
                    id=stream_raw.id,
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
                self._logger.log_debug(f"Стрим для {broadcaster_id}: онлайн")
                return StreamStatusDTO(is_online=True, stream_data=stream_data)
            self._logger.log_debug(f"Стрим для {broadcaster_id}: офлайн")
            return StreamStatusDTO(is_online=False, stream_data=None)
        except httpx.TimeoutException:
            self._logger.log_error(f"Таймаут при получении статуса стрима {broadcaster_id}")
            return None
        except httpx.RequestError as e:
            self._logger.log_error(f"Ошибка соединения при получении статуса стрима {broadcaster_id}: {e}")
            return None
        except Exception as e:
            self._logger.log_error(f"Неожиданная ошибка при получении статуса стрима {broadcaster_id}: {e}")
            return None

    async def get_stream_info(self, channel_name: str) -> StreamInfoDTO | None:
        user = await self.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return None
        status = await self.get_stream_status(broadcaster_id)
        if not status or not status.is_online or not status.stream_data:
            return None
        return status.stream_data

    async def _get_user_followage(self, broadcaster_id: str, user_id: str) -> FollowageInfo | None:
        response = await self._api_client.get(url="/channels/followers", params={"broadcaster_id": broadcaster_id, "user_id": user_id})
        try:
            data = await handle_api_response(response, f"get_user_followage({broadcaster_id}, {user_id})")
            parsed: FollowersResponse = FollowersResponse.model_validate(data)
        except ValidationError:
            return None

        followers: list[FollowerData] = parsed.data
        if followers:
            follow_data = followers[0]
            follow_dt = follow_data.followed_at.replace(tzinfo=None)
            return FollowageInfo(
                user_id=follow_data.user_id,
                user_name=follow_data.user_name,
                user_login=follow_data.user_login,
                followed_at=follow_dt,
            )
        return None

    async def get_followage(self, channel_name: str, user_name: str) -> FollowageInfo | None:
        broadcaster = await self.get_user_by_login(channel_name)
        user = await self.get_user_by_login(user_name)
        broadcaster_id = None if broadcaster is None else broadcaster.id
        user_id = None if user is None else user.id
        if not broadcaster_id or not user_id:
            return None
        return await self._get_user_followage(broadcaster_id=broadcaster_id, user_id=user_id)

    async def _get_channel_followers(self, broadcaster_id: str) -> list[ChannelFollowerDTO]:
        params = {"broadcaster_id": broadcaster_id, "first": 100}
        followers: list[ChannelFollowerDTO] = []
        cursor = None

        while True:
            if cursor:
                params["after"] = cursor
            elif "after" in params:
                params.pop("after")

            response = await self._api_client.get(url="/channels/followers", params=params)
            try:
                data = await handle_api_response(response, f"get_channel_followers({broadcaster_id})")
                parsed: FollowersResponse = FollowersResponse.model_validate(data)
                followers_page: list[FollowerData] = parsed.data
            except ValidationError:
                break

            followers.extend(
                [
                    ChannelFollowerDTO(
                        user_id=item.user_id,
                        user_name=item.user_login,
                        display_name=item.user_name,
                        followed_at=item.followed_at.replace(tzinfo=None),
                    )
                    for item in followers_page
                ]
            )

            pagination = data.get("pagination") if isinstance(data, dict) else None
            cursor = None if not pagination else pagination.get("cursor")
            if not cursor or not parsed.data:
                break

        return followers

    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]:
        user = await self.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return []
        return await self._get_channel_followers(broadcaster_id=broadcaster_id)
