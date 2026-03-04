from __future__ import annotations

from contextlib import contextmanager

from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.intent.application.uow.intent_uow import IntentUnitOfWork, IntentUnitOfWorkFactory
from app.ai.intent.domain.intent_detector import IntentDetectorClient


class SimpleIntentUnitOfWork(IntentUnitOfWork):
    def __init__(self, intent_detector: IntentDetectorClient, llm_repository: LLMRepository):
        self._intent_detector = intent_detector
        self._llm_repository = llm_repository

    @property
    def intent_detector(self) -> IntentDetectorClient:
        return self._intent_detector

    @property
    def llm_repository(self) -> LLMRepository:
        return self._llm_repository

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class SimpleIntentUnitOfWorkFactory(IntentUnitOfWorkFactory):
    def __init__(self, intent_detector: IntentDetectorClient, llm_repository: LLMRepository):
        self._intent_detector = intent_detector
        self._llm_repository = llm_repository

    def create(self, read_only: bool = False):
        @contextmanager
        def _ctx():
            yield SimpleIntentUnitOfWork(self._intent_detector, self._llm_repository)

        return _ctx()
