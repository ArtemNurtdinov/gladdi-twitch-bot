from dataclasses import dataclass

from app.core.config.domain.model.application import ApplicationConfig
from app.core.config.domain.model.db import DatabaseConfig
from app.core.config.domain.model.intent_detector import IntentDetectorConfig
from app.core.config.domain.model.llmbox import LLMBoxConfig
from app.core.config.domain.model.logging import LoggingConfig
from app.core.config.domain.model.telegram import TelegramConfig
from app.core.config.domain.model.twitch import TwitchConfig


@dataclass(frozen=True)
class Config:
    application: ApplicationConfig
    db: DatabaseConfig
    logging: LoggingConfig
    telegram: TelegramConfig
    twitch: TwitchConfig
    llmbox: LLMBoxConfig
    intent_detector: IntentDetectorConfig
