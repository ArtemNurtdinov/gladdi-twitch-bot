import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TelegramConfig:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    group_id: int = int(os.getenv("TELEGRAM_GROUP_ID", "0"))


@dataclass
class TwitchConfig:
    client_id: str = os.getenv("TWITCH_CLIENT_ID", "")
    client_secret: str = os.getenv("TWITCH_CLIENT_SECRET", "")
    redirect_url: str = os.getenv("TWITCH_REDIRECT_URL", "http://localhost:5000")
    channel_name: str = os.getenv("TWITCH_CHANNEL", "artemnefrit")
    access_token: str = os.getenv("TWITCH_ACCESS_TOKEN", "")
    refresh_token: str = os.getenv("TWITCH_REFRESH_TOKEN", "")


@dataclass
class DashboardConfig:
    host: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port: int = int(os.getenv("DASHBOARD_PORT", "8000"))
    log_level: str = os.getenv("DASHBOARD_LOG_LEVEL", "info")


@dataclass
class DatabaseConfig:
    url: str = os.getenv("DATABASE_URL", "")


@dataclass
class LoggingConfig:
    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: str = os.getenv("LOG_FILE", "gladdi-twitch-bot.log")
    format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class LLMBoxConfig:
    host = os.getenv("LLMBOX_DOMAIN")


@dataclass
class IntentDetectorConfig:
    host = os.getenv("INTENT_DETECTOR_DOMAIN")


@dataclass
class Config:
    telegram: TelegramConfig
    twitch: TwitchConfig
    dashboard: DashboardConfig
    database: DatabaseConfig
    logging: LoggingConfig
    llmbox: LLMBoxConfig
    intent_detector: IntentDetectorConfig


def load_config() -> Config:
    return Config(
        telegram=TelegramConfig(),
        twitch=TwitchConfig(),
        dashboard=DashboardConfig(),
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        llmbox=LLMBoxConfig(),
        intent_detector=IntentDetectorConfig()
    )


def validate_config(config: Config) -> bool:
    errors = []

    if not config.telegram.bot_token:
        errors.append("❌ Не установлен TELEGRAM_BOT_TOKEN")

    if not config.twitch.client_id:
        errors.append("❌ Не установлен TWITCH_CLIENT_ID")

    if not config.twitch.client_secret:
        errors.append("❌ Не установлен TWITCH_CLIENT_SECRET")

    if errors:
        print("Ошибки конфигурации:")
        for error in errors:
            print(error)
        return False

    return True


config = load_config()
