from __future__ import annotations

from app.core.network.api.client import ApiClient
from app.platform.auth.platform_auth import PlatformAuth


class TwitchHelixClient(ApiClient):
    _HEADER_CLIENT_ID = "Client-ID"
    _HEADER_AUTHORIZATION = "Authorization"

    def __init__(self, auth: PlatformAuth):
        super().__init__(base_url="https://api.twitch.tv/helix")
        self._auth = auth

    def base_headers(self) -> dict[str, str] | None:
        return {self._HEADER_CLIENT_ID: self._auth.client_id, self._HEADER_AUTHORIZATION: f"Bearer {self._auth.access_token}"}
