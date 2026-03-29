from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.config_source import ConfigSource
from app.core.config.domain.model.application import ApplicationConfig
from app.core.config.domain.model.configuration import Config
from app.core.config.domain.model.db import DatabaseConfig
from app.core.config.domain.model.intent_detector import IntentDetectorConfig
from app.core.config.domain.model.llmbox import LLMBoxConfig
from app.core.config.domain.model.logging import LoggingConfig
from app.core.config.domain.model.telegram import TelegramConfig
from app.core.config.domain.model.twitch import TwitchConfig


class ConfigRepositoryImpl(ConfigRepository):
    def __init__(self, config_source: ConfigSource):
        self._config_source = config_source

    def get_config(self) -> Config:
        return Config(
            application=ApplicationConfig(
                host=self._config_source.get_str("HOST", "0.0.0.0"),
                port=self._config_source.get_int("PORT", 8003),
                auth_secret=self._config_source.get_str("ACCESS_SECRET_KEY"),
                auth_secret_algorithm=self._config_source.get_str("ACCESS_SECRET_ALGORITHM"),
                access_token_expire_minutes=self._config_source.get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 30),
            ),
            db=DatabaseConfig(url=self._config_source.get_str("DATABASE_URL")),
            logging=LoggingConfig(
                level=self._config_source.get_str("LOG_LEVEL", "INFO"),
                file=self._config_source.get_str("LOG_FILE", "gladdi-twitch-bot.log"),
                format=self._config_source.get_str("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            ),
            telegram=TelegramConfig(
                bot_token=self._config_source.get_str("TELEGRAM_BOT_TOKEN"), group_id=self._config_source.get_int("TELEGRAM_GROUP_ID")
            ),
            twitch=TwitchConfig(
                client_id=self._config_source.get_str("TWITCH_CLIENT_ID"),
                client_secret=self._config_source.get_str("TWITCH_CLIENT_SECRET"),
                redirect_url=self._config_source.get_str("TWITCH_REDIRECT_URL"),
                channel_name=self._config_source.get_str("TWITCH_CHANNEL"),
            ),
            llmbox=LLMBoxConfig(host=self._config_source.get_str("LLMBOX_DOMAIN")),
            intent_detector=IntentDetectorConfig(host=self._config_source.get_str("INTENT_DETECTOR_DOMAIN")),
        )
