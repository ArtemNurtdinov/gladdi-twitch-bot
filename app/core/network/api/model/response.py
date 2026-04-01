from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    text: str
    json_data: Any
