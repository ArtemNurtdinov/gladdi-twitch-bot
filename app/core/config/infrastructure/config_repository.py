from dotenv import load_dotenv

from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.config_source import ConfigSource
from app.core.config.domain.model.application import ApplicationConfig
from app.core.config.domain.model.bot import BotConfig
from app.core.config.domain.model.configuration import Config
from app.core.config.domain.model.db import DatabaseConfig
from app.core.config.domain.model.intent_detector import IntentDetectorConfig
from app.core.config.domain.model.llmbox import LLMBoxConfig
from app.core.config.domain.model.logging import LoggingConfig
from app.core.config.domain.model.telegram import TelegramConfig
from app.core.config.domain.model.twitch import TwitchConfig


class ConfigRepositoryImpl(ConfigRepository):
    _COMMAND_PREFIX = "COMMAND_PREFIX"
    _COMMAND_ROLL = "COMMAND_ROLL"
    _COMMAND_FOLLOWAGE = "COMMAND_FOLLOWAGE"
    _COMMAND_ASK = "COMMAND_ASK"
    _COMMAND_FIGHT = "COMMAND_FIGHT"
    _COMMAND_BALANCE = "COMMAND_BALANCE"
    _COMMAND_BONUS = "COMMAND_BONUS"
    _COMMAND_TRANSFER = "COMMAND_TRANSFER"
    _COMMAND_SHOP = "COMMAND_SHOP"
    _COMMAND_BUY = "COMMAND_BUY"
    _COMMAND_EQUIPMENT = "COMMAND_EQUIPMENT"
    _COMMAND_TOP = "COMMAND_TOP"
    _COMMAND_BOTTOM = "COMMAND_BOTTOM"
    _COMMAND_STATS = "COMMAND_STATS"
    _COMMAND_GUESS = "COMMAND_GUESS"
    _COMMAND_GUESS_LETTER = "COMMAND_GUESS_LETTER"
    _COMMAND_GUESS_WORD = "COMMAND_GUESS_WORD"
    _COMMAND_RPS = "COMMAND_RPS"
    _COMMAND_HELP = "COMMAND_HELP"

    def __init__(self, config_source: ConfigSource):
        self._config_source = config_source
        load_dotenv()

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
            ),
            llmbox=LLMBoxConfig(host=self._config_source.get_str("LLMBOX_DOMAIN")),
            intent_detector=IntentDetectorConfig(host=self._config_source.get_str("INTENT_DETECTOR_DOMAIN")),
            bot=BotConfig(
                prefix=self._config_source.get_str(self._COMMAND_PREFIX),
                command_roll=self._config_source.get_str(self._COMMAND_ROLL),
                command_followage=self._config_source.get_str(self._COMMAND_FOLLOWAGE),
                command_gladdi=self._config_source.get_str(self._COMMAND_ASK),
                command_fight=self._config_source.get_str(self._COMMAND_FIGHT),
                command_balance=self._config_source.get_str(self._COMMAND_BALANCE),
                command_bonus=self._config_source.get_str(self._COMMAND_BONUS),
                command_transfer=self._config_source.get_str(self._COMMAND_TRANSFER),
                command_shop=self._config_source.get_str(self._COMMAND_SHOP),
                command_buy=self._config_source.get_str(self._COMMAND_BUY),
                command_equipment=self._config_source.get_str(self._COMMAND_EQUIPMENT),
                command_top=self._config_source.get_str(self._COMMAND_TOP),
                command_bottom=self._config_source.get_str(self._COMMAND_BOTTOM),
                command_stats=self._config_source.get_str(self._COMMAND_STATS),
                command_guess=self._config_source.get_str(self._COMMAND_GUESS),
                command_guess_letter=self._config_source.get_str(self._COMMAND_GUESS_LETTER),
                command_guess_word=self._config_source.get_str(self._COMMAND_GUESS_WORD),
                command_rps=self._config_source.get_str(self._COMMAND_RPS),
                command_help=self._config_source.get_str(self._COMMAND_HELP),
            ),
        )
