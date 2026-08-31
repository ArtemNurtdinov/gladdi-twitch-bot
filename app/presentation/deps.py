from fastapi import Depends, Request

from app.bootstrap.app_container import AppContainer
from app.core.config.domain.model.configuration import Config
from app.core.logger.domain.logger import Logger


def get_app(request: Request) -> AppContainer:
    return request.app.state.app


def get_logger(app: AppContainer = Depends(get_app)) -> Logger:
    return app.logger


def get_config(app: AppContainer = Depends(get_app)) -> Config:
    return app.config
