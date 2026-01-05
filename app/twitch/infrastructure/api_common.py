from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def handle_api_response(response: httpx.Response, operation: str) -> dict[str, Any]:
    if response.status_code == 200:
        logger.debug(f"API операция '{operation}' выполнена успешно")
        return response.json()
    logger.error(f"Ошибка в API операции '{operation}': {response.status_code}, {response.text}")
    raise Exception(f"API операция '{operation}' завершилась с ошибкой: {response.status_code}")

