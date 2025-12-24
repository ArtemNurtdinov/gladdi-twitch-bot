from logging import Logger

import httpx

from core.config import config


class TwitchAuth:
    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        logger: Logger
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = config.twitch.client_id
        self.client_secret = config.twitch.client_secret
        self.logger = logger

    async def update_access_token(self):
        self.logger.info("updating access token")
        url = 'https://id.twitch.tv/oauth2/token'

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, data=data)
        token_data = response.json()

        if 'access_token' in token_data:
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token', self.refresh_token)
        else:
            raise Exception('Ошибка обновления токена:', token_data)

    async def check_token_is_valid(self) -> bool:
        if not self.access_token:
            raise ValueError("Access token пуст")

        url = 'https://id.twitch.tv/oauth2/validate'
        headers = {'Authorization': f'OAuth {self.access_token}'}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            token_info = response.json()
            expires_in = token_info["expires_in"]
            self.logger.info("Токен действителен")
            return expires_in > 4000
        elif response.status_code == 401:
            self.logger.info("Токен истек или недействителен.")
            self.logger.info("Ответ от сервера:", response.json())
        else:
            self.logger.info("Произошла ошибка при проверке токена.")
            self.logger.info("Статус код:", response.status_code)
            self.logger.info("Ответ от сервера:", response.json())
        return False
