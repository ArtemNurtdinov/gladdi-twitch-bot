from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StreamingApiResponse:
    status_code: int
    text: str
    json_data: Any


class StreamingApiClient(ABC):

    @abstractmethod
    async def get(
        self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None
    ) -> StreamingApiResponse: ...

    @abstractmethod
    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> StreamingApiResponse: ...

    @abstractmethod
    async def aclose(self) -> None: ...
