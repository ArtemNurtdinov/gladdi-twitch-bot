import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from app.core.config.domain.model.logging import LoggingConfig
from app.core.logger.domain.logger import Logger


class LoggerImpl(Logger):
    def __init__(self, tag: str, config: LoggingConfig = None):
        self._logger = logging.getLogger(tag)
        self._config = config

        if config:
            self._setup_handlers(config)

    def _setup_handlers(self, config: LoggingConfig):
        if self._logger.handlers:
            return

        self._logger.setLevel(config.level)

        file_handler = TimedRotatingFileHandler(
            filename=config.file,
            when="H",
            interval=8,
            backupCount=2,
            utc=False,
            encoding="utf-8",
        )
        file_handler.setLevel(config.level)
        file_formatter = logging.Formatter(config.format)
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(config.level)
        console_formatter = logging.Formatter(config.format)
        console_handler.setFormatter(console_formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def log_debug(self, message: str):
        self._logger.debug(message)

    def log_info(self, message: str):
        self._logger.info(message)

    def log_error(self, message: str):
        self._logger.error(message)

    def log_exception(self, message: str, exception: Exception):
        self._logger.error(message, exception, exc_info=True)

    def create_child(self, child_tag: str) -> Logger:
        return LoggerImpl(tag=child_tag, config=self._config)
