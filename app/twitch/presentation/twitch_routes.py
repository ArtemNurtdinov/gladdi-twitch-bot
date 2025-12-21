import requests
import logging
from fastapi import APIRouter, HTTPException

from app.twitch.presentation.bot_manager import BotManager
from core.config import config
from app.twitch.presentation.twitch_schemas import AuthStartResponse, BotActionResult, BotStatus
from urllib.parse import urlencode

AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

PERMISSIONS_SCOPE = "chat:read chat:edit user:read:follows moderator:read:followers moderator:manage:banned_users moderator:read:chatters"

router = APIRouter(prefix="/bot")

bot_manager = BotManager()


@router.get("/status", summary="Получить состояние бота", response_model=BotStatus)
async def get_bot_status() -> BotStatus:
    return bot_manager.get_status()


@router.post("/start", summary="Начать авторизацию Twitch", response_model=AuthStartResponse)
async def start_authorization() -> AuthStartResponse:
    params = {
        "client_id": config.twitch.client_id,
        "redirect_uri": config.twitch.redirect_url,
        "response_type": "code",
        "scope": PERMISSIONS_SCOPE,
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    return AuthStartResponse(auth_url=auth_url, message="Откройте ссылку, авторизуйтесь — Twitch вернёт вас на redirect_uri, где бот заберёт code")


@router.get(
    "/callback",
    summary="OAuth callback от Twitch: обменивает code и запускает бота",
    response_model=BotActionResult,
)
async def oauth_callback(code: str | None = None, state: str | None = None) -> BotActionResult:
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
        response = requests.post(TOKEN_URL, data=data, timeout=10)
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
async def stop_bot() -> BotActionResult:
    try:
        return await bot_manager.stop_bot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки бота: {e}")
