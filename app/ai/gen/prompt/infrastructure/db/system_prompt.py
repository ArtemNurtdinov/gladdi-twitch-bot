from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.ai.gen.prompt.domain.models.system_prompt import SystemPrompt
from core.db import Base


class SystemPromptRow(Base):
    __tablename__ = "system_prompts"

    channel_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> SystemPrompt:
        return SystemPrompt(channel_name=str(self.channel_name), prompt=str(self.content))
