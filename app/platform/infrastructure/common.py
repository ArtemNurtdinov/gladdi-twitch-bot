from __future__ import annotations

from typing import Any

from app.core.logger.domain.logger import Logger
from app.core.network.api.model.response import ApiResponse


async def handle_api_response(response: ApiResponse, operation: str, logger: Logger) -> dict[str, Any]:
    if response.status_code == 200:
        logger.log_debug(f"API операция '{operation}' выполнена успешно")
        return response.json_data
    logger.log_error(f"Ошибка в API операции '{operation}': {response.status_code}, {response.text}")
    raise Exception(f"API операция '{operation}' завершилась с ошибкой: {response.status_code}")
