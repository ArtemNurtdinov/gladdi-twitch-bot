from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.network.api.model.response import ApiResponse


class ApiClient(ABC):
    _TIMEOUT_SECONDS_DEFAULT = 10.0
    _MAX_CONNECTIONS_DEFAULT = 20
    _MAX_KEEP_ALIVIE_CONNECTIONS_DEFAULT = 10

    def __init__(self, base_url: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(self._TIMEOUT_SECONDS_DEFAULT),
            limits=httpx.Limits(
                max_connections=self._MAX_CONNECTIONS_DEFAULT, max_keepalive_connections=self._MAX_KEEP_ALIVIE_CONNECTIONS_DEFAULT
            ),
        )

    @abstractmethod
    def base_headers(self) -> dict[str, str] | None: ...

    async def get(self, url: str, params: dict[str, Any] | None, headers: dict[str, str] | None = None) -> ApiResponse:
        base_headers = self.base_headers()
        merged_headers = {**base_headers, **headers} if headers else base_headers
        response = await self._client.get(url, params=params, headers=merged_headers)
        return ApiResponse(status_code=response.status_code, text=response.text, json_data=response.json())

    async def post(
        self, url: str, params: dict[str, Any] | None, headers: dict[str, str] | None, data: dict[str, Any] | None
    ) -> ApiResponse:
        base_headers = self.base_headers()
        merged_headers = {**base_headers, **headers} if headers else base_headers
        response = await self._client.post(url, params=params, headers=merged_headers, json=data)
        return ApiResponse(status_code=response.status_code, text=response.text, json_data=response.json())

    async def aclose(self) -> None:
        await self._client.aclose()
