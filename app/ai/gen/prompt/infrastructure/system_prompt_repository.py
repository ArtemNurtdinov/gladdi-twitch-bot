from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gen.prompt.infrastructure.db.system_prompt import SystemPromptRow
from app.ai.gen.prompt.domain.models.system_prompt import SystemPrompt
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository


class SystemPromptRepositoryImpl(SystemPromptRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_system_prompt(self, channel_name: str) -> SystemPrompt | None:
        statement = select(SystemPromptRow).where(SystemPromptRow.channel_name == channel_name)
        row: SystemPromptRow | None = self._session.execute(statement).scalar_one_or_none()
        if row is None:
            return None
        return row.to_domain()

    def save_system_prompt(self, system_prompt: SystemPrompt) -> None:
        row = (
            self._session.execute(select(SystemPromptRow).where(SystemPromptRow.channel_name == system_prompt.channel_name))
            .scalars()
            .first()
        )
        if row:
            row.content = system_prompt.prompt
            row.updated_at = datetime.utcnow()
        else:
            self._session.add(
                SystemPromptRow(channel_name=system_prompt.channel_name, content=system_prompt.prompt, updated_at=datetime.utcnow())
            )
