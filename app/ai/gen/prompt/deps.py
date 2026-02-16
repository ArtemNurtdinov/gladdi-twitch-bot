"""Зависимости для API эндпоинтов (системный промпт)."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.gen.prompt.application.get_system_prompt_use_case import GetSystemPromptUseCase
from app.ai.gen.prompt.application.update_system_prompt_use_case import UpdateSystemPromptUseCase
from app.ai.gen.infrastructure.system_prompt_repository import SystemPromptRepository
from core.db import get_db_ro, get_db_rw


def get_get_system_prompt_use_case(
    db: Session = Depends(get_db_ro),
) -> GetSystemPromptUseCase:
    return GetSystemPromptUseCase(SystemPromptRepository(db))


def get_update_system_prompt_use_case(
    db: Session = Depends(get_db_rw),
) -> UpdateSystemPromptUseCase:
    return UpdateSystemPromptUseCase(SystemPromptRepository(db))
