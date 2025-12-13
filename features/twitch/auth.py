import logging

import requests

from config import config

logger = logging.getLogger(__name__)

class TwitchAuth:
    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id or config.twitch.client_id
        self.client_secret = client_secret or config.twitch.client_secret

    def update_access_token(self):
        logger.info("updating access token")
        url = 'https://id.twitch.tv/oauth2/token'

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        response = requests.post(url, data=data)
        token_data = response.json()

        if 'access_token' in token_data:
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token', self.refresh_token)
        else:
            raise Exception('Ошибка обновления токена:', token_data)

    def check_token_is_valid(self) -> bool:
        if not self.access_token:
            raise ValueError("Access token пуст")

        url = 'https://id.twitch.tv/oauth2/validate'
        headers = {'Authorization': f'OAuth {self.access_token}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            token_info = response.json()
            expires_in = token_info["expires_in"]
            logger.info("Токен действителен")
            return expires_in > 4000
        elif response.status_code == 401:
            logger.info("Токен истек или недействителен.")
            logger.info("Ответ от сервера:", response.json())
        else:
            logger.info("Произошла ошибка при проверке токена.")
            logger.info("Статус код:", response.status_code)
            logger.info("Ответ от сервера:", response.json())
        return False
