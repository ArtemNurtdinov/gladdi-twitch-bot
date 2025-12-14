from typing import Optional
from dataclasses import dataclass


@dataclass
class TransferResult:
    success: bool
    message: Optional[str] = None

    @classmethod
    def success_result(cls) -> 'TransferResult':
        return cls(success=True)

    @classmethod
    def failure_result(cls, message: str) -> 'TransferResult':
        return cls(success=False, message=message)
