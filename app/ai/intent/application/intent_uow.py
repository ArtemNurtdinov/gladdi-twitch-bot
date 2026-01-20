from __future__ import annotations

from typing import Protocol

from app.ai.gen.llm.domain.llm_client_port import LLMClientPort
from app.ai.intent.domain.intent_detector import IntentDetectorClient
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class IntentUnitOfWork(UnitOfWork, Protocol):
    @property
    def intent_detector(self) -> IntentDetectorClient: ...

    @property
    def llm_client(self) -> LLMClientPort: ...


class IntentUnitOfWorkFactory(UnitOfWorkFactory[IntentUnitOfWork], Protocol):
    pass
