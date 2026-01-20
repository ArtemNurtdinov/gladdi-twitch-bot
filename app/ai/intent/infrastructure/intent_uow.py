from __future__ import annotations

from contextlib import contextmanager

from app.ai.gen.llm.domain.llm_client_port import LLMClientPort
from app.ai.intent.application.intent_uow import IntentUnitOfWork, IntentUnitOfWorkFactory
from app.ai.intent.domain.intent_detector import IntentDetectorClient


class SimpleIntentUnitOfWork(IntentUnitOfWork):
    def __init__(self, intent_detector: IntentDetectorClient, llm_client: LLMClientPort):
        self._intent_detector = intent_detector
        self._llm_client = llm_client

    @property
    def intent_detector(self) -> IntentDetectorClient:
        return self._intent_detector

    @property
    def llm_client(self) -> LLMClientPort:
        return self._llm_client

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class SimpleIntentUnitOfWorkFactory(IntentUnitOfWorkFactory):
    def __init__(self, intent_detector: IntentDetectorClient, llm_client: LLMClientPort):
        self._intent_detector = intent_detector
        self._llm_client = llm_client

    def create(self, read_only: bool = False):
        @contextmanager
        def _ctx():
            yield SimpleIntentUnitOfWork(self._intent_detector, self._llm_client)

        return _ctx()
