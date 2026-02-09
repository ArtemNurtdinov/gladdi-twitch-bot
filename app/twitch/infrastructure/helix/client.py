from __future__ import annotations

from typing import Any

import httpx

from app.twitch.infrastructure.helix.auth import TwitchAuth
from core.platform.api_client import StreamingApiClient, StreamingApiResponse


class TwitchHelixClient(StreamingApiClient):
    def __init__(self, twitch_auth: TwitchAuth):
        self._twitch_auth = twitch_auth
        self._client = httpx.AsyncClient(
            base_url="https://api.twitch.tv/helix",
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        base = {"Client-ID": self._twitch_auth.client_id, "Authorization": f"Bearer {self._twitch_auth.access_token}"}
        if extra:
            base.update(extra)
        return base

    async def get(self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> StreamingApiResponse:
        response = await self._client.get(url, params=params, headers=self._headers(headers))
        return StreamingApiResponse(
            status_code=response.status_code,
            text=response.text,
            json_data=response.json(),
        )

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> StreamingApiResponse:
        merged_headers = self._headers(headers)
        response = await self._client.post(url, params=params, headers=merged_headers, json=json)
        return StreamingApiResponse(
            status_code=response.status_code,
            text=response.text,
            json_data=response.json(),
        )

    async def aclose(self) -> None:
        await self._client.aclose()
