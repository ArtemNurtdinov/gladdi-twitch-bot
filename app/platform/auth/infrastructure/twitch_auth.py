import httpx

from app.core.logger.domain.logger import Logger
from app.platform.auth.platform_auth import PlatformAuth


class TwitchAuth(PlatformAuth):
    _TWITCH_OAUTH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    _TWITCH_OAUTH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
    _API_CLIENT_TIMEOUT_SECONDS = 10
    _TOKEN_EXPIRY_THRESHOLD_SECONDS = 4000

    def __init__(self, client_id: str, client_secret: str, logger: Logger):
        super().__init__(client_id, client_secret)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._API_CLIENT_TIMEOUT_SECONDS),
        )
        self.logger = logger.create_child(__name__)

    async def update_access_token(self) -> None:
        self.logger.log_info("updating access token")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        response = await self._client.post(self._TWITCH_OAUTH_TOKEN_URL, data=data)
        token_data = response.json()

        if "access_token" in token_data:
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token", self.refresh_token)
            self.update_tokens(access_token, refresh_token)
        else:
            raise Exception("Ошибка обновления токена:", token_data)

    async def check_token_is_valid(self) -> bool:
        headers = {"Authorization": f"OAuth {self.access_token}"}
        response = await self._client.get(self._TWITCH_OAUTH_VALIDATE_URL, headers=headers)
        if response.status_code == 200:
            token_info = response.json()
            expires_in = token_info["expires_in"]
            return expires_in > self._TOKEN_EXPIRY_THRESHOLD_SECONDS
        elif response.status_code == 401:
            self.logger.log_info(f"Токен истек или недействителен.{response.json()}")
        else:
            self.logger.log_info(f"Произошла ошибка при проверке токена.{response.json()}")
        return False
