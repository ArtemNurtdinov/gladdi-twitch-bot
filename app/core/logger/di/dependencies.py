from app.core.config.domain.model.logging import LoggingConfig
from app.core.logger.domain.logger import Logger
from app.core.logger.infrastructure.logger import LoggerImpl


def provide_logger(config: LoggingConfig) -> Logger:
    return LoggerImpl("bootstrap", config)
