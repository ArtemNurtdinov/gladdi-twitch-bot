import logging
from functools import lru_cache
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.platform.auth import PlatformAuth
from app.platform.bot.bot_manager import BotManager
from app.platform.bot.bot_settings import DEFAULT_SETTINGS, BotSettings, build_bot_settings
from app.platform.bot.schemas import BotActionResult, BotStatus
from app.twitch.bootstrap.router_factory import build_twitch_command_router
from app.twitch.bootstrap.twitch import build_twitch_providers
from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.twitch_chat_client import TwitchChatClient
from app.twitch.presentation.twitch_schemas import AuthStartResponse
from bootstrap.config_provider import get_config
from core.chat.outbound import ChatOutbound

AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

PERMISSIONS_SCOPE = "chat:read chat:edit user:read:follows moderator:read:followers moderator:manage:banned_users moderator:read:chatters"

router = APIRouter(prefix="/bot")


def get_bot_settings(cfg=Depends(get_config)) -> BotSettings:
    return build_bot_settings(cfg)


@lru_cache
def get_bot_manager(settings: BotSettings = Depends(get_bot_settings)) -> BotManager:
    return BotManager(
        platform_auth_factory=_twitch_auth_factory,
        platform_providers_builder=build_twitch_providers,
        chat_client_factory=_twitch_chat_client_factory,
        command_router_builder=build_twitch_command_router,
        settings=settings,
    )


def _twitch_auth_factory(access_token: str, refresh_token: str) -> TwitchAuth:
    return TwitchAuth(access_token=access_token, refresh_token=refresh_token, logger=logging.getLogger(__name__))


def _twitch_chat_client_factory(auth: PlatformAuth, settings: BotSettings = DEFAULT_SETTINGS) -> ChatOutbound:
    twitch_auth: TwitchAuth = auth  # type: ignore[assignment]
    return TwitchChatClient(twitch_auth=twitch_auth, settings=settings)


@router.get("/status", summary="Получить состояние бота", response_model=BotStatus)
async def get_bot_status(bot_manager: BotManager = Depends(get_bot_manager)) -> BotStatus:
    return bot_manager.get_status()


@router.post("/start", summary="Начать авторизацию Twitch", response_model=AuthStartResponse)
async def start_authorization(cfg=Depends(get_config)) -> AuthStartResponse:
    params = {
        "client_id": cfg.twitch.client_id,
        "redirect_uri": cfg.twitch.redirect_url,
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
    cfg=Depends(get_config),
    bot_manager: BotManager = Depends(get_bot_manager),
) -> BotActionResult:
    if not code:
        raise HTTPException(status_code=400, detail="Не передан параметр 'code'")
    try:
        data = {
            "client_id": cfg.twitch.client_id,
            "client_secret": cfg.twitch.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": cfg.twitch.redirect_url,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(TOKEN_URL, data=data)
        if response.status_code != 200:
            logging.error("Не удалось получить токены: %s", response.text)
            raise ValueError(f"Не удалось получить токены: {response.text}")
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token or not refresh_token:
            raise ValueError("Не удалось получить токены по переданному коду")

        return await bot_manager.start_bot(access_token=access_token, refresh_token=refresh_token)
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
