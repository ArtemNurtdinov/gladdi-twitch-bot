import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ApplicationConfig:
    auth_secret: str = os.getenv("ACCESS_SECRET_KEY")
    auth_secret_algorithm: str = os.getenv("ACCESS_SECRET_ALGORITHM", "")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 30))


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    group_id: int = int(os.getenv("TELEGRAM_GROUP_ID", "0"))


@dataclass(frozen=True)
class TwitchConfig:
    client_id: str = os.getenv("TWITCH_CLIENT_ID", "")
    client_secret: str = os.getenv("TWITCH_CLIENT_SECRET", "")
    redirect_url: str = os.getenv("TWITCH_REDIRECT_URL", "http://localhost:8003/api/v1/bot/callback")
    channel_name: str = os.getenv("TWITCH_CHANNEL", "artemnefrit")


@dataclass(frozen=True)
class DashboardConfig:
    host: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port: int = int(os.getenv("DASHBOARD_PORT", "8003"))
    log_level: str = os.getenv("DASHBOARD_LOG_LEVEL", "info")


@dataclass(frozen=True)
class DatabaseConfig:
    url: str = os.getenv("DATABASE_URL", "")


@dataclass(frozen=True)
class LoggingConfig:
    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: str = os.getenv("LOG_FILE", "../gladdi-twitch-bot.log")
    format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass(frozen=True)
class LLMBoxConfig:
    host = os.getenv("LLMBOX_DOMAIN")


@dataclass(frozen=True)
class IntentDetectorConfig:
    host = os.getenv("INTENT_DETECTOR_DOMAIN")


@dataclass(frozen=True)
class Config:
    application: ApplicationConfig
    telegram: TelegramConfig
    twitch: TwitchConfig
    dashboard: DashboardConfig
    database: DatabaseConfig
    logging: LoggingConfig
    llmbox: LLMBoxConfig
    intent_detector: IntentDetectorConfig


def validate_config(config: Config) -> list[str]:
    errors: list[str] = []

    if not config.application.auth_secret:
        errors.append("Не установлен ACCESS_SECRET_KEY")

    if not config.application.auth_secret_algorithm:
        errors.append("Не установлен ACCESS_SECRET_ALGORITHM")

    if not config.telegram.bot_token:
        errors.append("Не установлен TELEGRAM_BOT_TOKEN")

    if not config.telegram.group_id:
        errors.append("Не установлен TELEGRAM_GROUP_ID")

    if not config.twitch.client_id:
        errors.append("Не установлен TWITCH_CLIENT_ID")

    if not config.twitch.client_secret:
        errors.append("Не установлен TWITCH_CLIENT_SECRET")

    if not config.twitch.redirect_url:
        errors.append("Не установлен TWITCH_REDIRECT_URL")

    if not config.twitch.channel_name:
        errors.append("Не установлен TWITCH_CHANNEL")

    if not config.database.url:
        errors.append("Не установлен DATABASE_URL")

    if not config.llmbox.host:
        errors.append("Не установлен LLMBOX_DOMAIN")

    if not config.intent_detector.host:
        errors.append("Не установлен INTENT_DETECTOR_DOMAIN")

    return errors


def load_config() -> Config:
    cfg = Config(
        application=ApplicationConfig(),
        telegram=TelegramConfig(),
        twitch=TwitchConfig(),
        dashboard=DashboardConfig(),
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        llmbox=LLMBoxConfig(),
        intent_detector=IntentDetectorConfig(),
    )

    errors = validate_config(cfg)
    if errors:
        raise RuntimeError("Ошибки конфигурации:\n" + "\n".join(errors))

    return cfg
