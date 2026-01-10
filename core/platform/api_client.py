from __future__ import annotations

from typing import Any, Protocol

import httpx


class StreamingApiClient(Protocol):
    async def get(self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> httpx.Response: ...

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response: ...

    async def aclose(self) -> None: ...
