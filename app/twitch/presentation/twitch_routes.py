from functools import lru_cache
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.config.di.composition import load_config
from app.core.config.domain.model.configuration import Config
from app.core.logger.di.composition import get_logger
from app.core.logger.domain.logger import Logger
from app.platform.bot.bot_manager import BotManager
from app.platform.bot.model.bot_settings import BotSettings, DefaultBotSettings
from app.platform.bot.schemas import BotActionResult, BotStatus
from app.twitch.presentation.twitch_schemas import AuthStartResponse

AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

PERMISSIONS_SCOPE = (
    "chat:read chat:edit "
    "user:read:follows "
    "moderator:read:followers moderator:manage:banned_users moderator:read:chatters "
    "user:read:chat user:write:chat user:bot channel:bot"
)

router = APIRouter()


@lru_cache
def get_bot_settings(config: Config = Depends(load_config)) -> BotSettings:
    group_id = config.telegram.group_id
    settings = DefaultBotSettings(group_id=group_id)
    return settings


@lru_cache
def get_bot_manager(settings: BotSettings = Depends(get_bot_settings), logger: Logger = Depends(get_logger)) -> BotManager:
    return BotManager(settings=settings, logger=logger)


@router.get("/status", summary="Получить состояние бота", response_model=BotStatus)
async def get_bot_status(bot_manager: BotManager = Depends(get_bot_manager)) -> BotStatus:
    return bot_manager.get_status()


@router.post("/start", summary="Начать авторизацию Twitch", response_model=AuthStartResponse)
async def start_authorization(config=Depends(load_config)) -> AuthStartResponse:
    params = {
        "client_id": config.twitch.client_id,
        "redirect_uri": config.twitch.redirect_url,
        "response_type": "code",
        "scope": PERMISSIONS_SCOPE,
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    return AuthStartResponse(
        auth_url=auth_url, message="Откройте ссылку, авторизуйтесь — Twitch вернёт вас на redirect_uri, где бот заберёт code"
    )


@router.get(
    "/callback",
    summary="OAuth callback от Twitch: обменивает code и запускает бота",
    response_model=BotActionResult,
)
async def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    config: Config = Depends(load_config),
    bot_manager: BotManager = Depends(get_bot_manager),
    logger: Logger = Depends(get_logger),
) -> BotActionResult:
    if not code:
        raise HTTPException(status_code=400, detail="Не передан параметр 'code'")
    try:
        data = {
            "client_id": config.twitch.client_id,
            "client_secret": config.twitch.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config.twitch.redirect_url,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(TOKEN_URL, data=data)
        if response.status_code != 200:
            raise ValueError(f"Не удалось получить токены: {response.text}")
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token or not refresh_token:
            raise ValueError("Не удалось получить токены по переданному коду")

        return await bot_manager.start_bot(
            access_token=access_token,
            refresh_token=refresh_token,
            tg_bot_token=config.telegram.bot_token,
            llmbox_host=config.llmbox.host,
            intent_detector_host=config.intent_detector.host,
            client_id=config.twitch.client_id,
            client_secret=config.twitch.client_secret,
            logger=logger,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки callback: {e}")


@router.post("/stop", summary="Остановить Twitch бота", response_model=BotActionResult)
async def stop_bot(bot_manager: BotManager = Depends(get_bot_manager)) -> BotActionResult:
    try:
        return await bot_manager.stop_bot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки бота: {e}")
