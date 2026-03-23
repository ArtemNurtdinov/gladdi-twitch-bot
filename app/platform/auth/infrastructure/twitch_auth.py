from logging import Logger

import httpx

from app.platform.auth.platform_auth import PlatformAuth


class TwitchAuth(PlatformAuth):
    _TWITCH_OAUTH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    _TWITCH_OAUTH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"

    def __init__(self, access_token: str, refresh_token: str, client_id: str, client_secret: str, logger: Logger):
        super().__init__(access_token, refresh_token, client_id, client_secret)
        self.logger = logger

    async def update_access_token(self):
        self.logger.info("updating access token")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self._TWITCH_OAUTH_TOKEN_URL, data=data)
        token_data = response.json()

        if "access_token" in token_data:
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token", self.refresh_token)
            self.update_tokens(access_token, refresh_token)
        else:
            raise Exception("Ошибка обновления токена:", token_data)

    async def check_token_is_valid(self) -> bool:
        headers = {"Authorization": f"OAuth {self.access_token}"}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self._TWITCH_OAUTH_VALIDATE_URL, headers=headers)

        if response.status_code == 200:
            token_info = response.json()
            expires_in = token_info["expires_in"]
            self.logger.info("Токен действителен")
            return expires_in > 4000
        elif response.status_code == 401:
            self.logger.info("Токен истек или недействителен.", response.json())
        else:
            self.logger.info("Произошла ошибка при проверке токена.", response.json())
        return False
