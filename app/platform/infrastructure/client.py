from __future__ import annotations

from typing import Any

import httpx

from app.platform.auth.platform_auth import PlatformAuth
from app.platform.infrastructure.api_client import StreamingApiClient, StreamingApiResponse


class TwitchHelixClient(StreamingApiClient):
    _HEADER_CLIENT_ID = "Client-ID"
    _HEADER_AUTHORIZATION = "Authorization"

    def __init__(self, auth: PlatformAuth):
        self._auth = auth
        self._client = httpx.AsyncClient(
            base_url="https://api.twitch.tv/helix",
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        base = {self._HEADER_CLIENT_ID: self._auth.client_id, self._HEADER_AUTHORIZATION: f"Bearer {self._auth.access_token}"}
        if extra:
            base.update(extra)
        return base

    async def get(self, url: str, params: dict[str, Any], headers: dict[str, str] | None = None):
        response = await self._client.get(url, params=params, headers=headers)
        return StreamingApiResponse(status_code=response.status_code, text=response.text, json_data=response.json())

    async def post(
        self,
        url: str,
        params: dict[str, Any],
        headers: dict[str, str],
        data: dict[str, Any],
    ) -> StreamingApiResponse:
        merged_headers = self._headers(headers)
        response = await self._client.post(url, params=params, headers=merged_headers, json=data)
        return StreamingApiResponse(status_code=response.status_code, text=response.text, json_data=response.json())

    async def aclose(self) -> None:
        await self._client.aclose()
