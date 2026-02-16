from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gen.infrastructure.db.system_prompt import SystemPromptRow


class SystemPromptRepository:
    def __init__(self, session: Session):
        self._session = session

    def get(self, channel_name: str) -> str | None:
        row = self._session.execute(select(SystemPromptRow).where(SystemPromptRow.channel_name == channel_name)).scalars().first()
        return row.content if row else None

    def set(self, channel_name: str, content: str) -> None:
        row = self._session.execute(select(SystemPromptRow).where(SystemPromptRow.channel_name == channel_name)).scalars().first()
        if row:
            row.content = content
            row.updated_at = datetime.utcnow()
        else:
            self._session.add(SystemPromptRow(channel_name=channel_name, content=content, updated_at=datetime.utcnow()))
