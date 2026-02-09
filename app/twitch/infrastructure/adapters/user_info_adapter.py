from __future__ import annotations

import logging

import httpx
from pydantic import ValidationError

from app.twitch.infrastructure.helix.models import UsersResponse
from app.user.application.model import UserInfoDTO
from app.user.application.user_info_port import UserInfoPort
from core.platform.api_client import StreamingApiClient

logger = logging.getLogger(__name__)


class UserInfoApiAdapter(UserInfoPort):
    def __init__(self, client: StreamingApiClient):
        self._client = client

    async def get_user_by_login(self, login: str) -> UserInfoDTO | None:
        logger.debug(f"Получение информации о пользователе для логина: {login}")
        try:
            response = await self._client.get("/users", params={"login": login})
            if response.status_code == 401:
                logger.error(f"Ошибка авторизации при получении пользователя {login}. Проверьте токен.")
                return None
            if response.status_code == 404:
                logger.warning(f"Пользователь {login} не найден")
                return None
            if response.status_code != 200:
                logger.error(f"API ошибка при получении пользователя {login}: {response.status_code}, {response.text}")
                return None

            try:
                parsed = UsersResponse.model_validate(response.json_data)
            except ValidationError as e:
                logger.error(f"Валидация пользователя {login} не прошла: {e}")
                return None

            if not parsed.data:
                logger.warning(f"Пользователь {login} не найден в ответе API")
                return None

            user_data = parsed.data[0]
            logger.debug(f"Информация о пользователе {login} получена")
            return UserInfoDTO(id=user_data.id, login=user_data.login, display_name=user_data.display_name)
        except httpx.TimeoutException:
            logger.error(f"Таймаут при получении пользователя {login}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения при получении пользователя {login}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении пользователя {login}: {e}")
            return None
