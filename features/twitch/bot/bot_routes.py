from fastapi import APIRouter, HTTPException

from authorize_twitch import build_auth_url, exchange_code_for_tokens
from features.twitch.bot.bot_manager import BotManager
from features.twitch.bot.bot_schemas import AuthStartResponse, BotActionResult, BotStatus

router = APIRouter(prefix="/bot", tags=["Bot"])

bot_manager = BotManager()


async def _start_bot_with_code(code: str) -> BotActionResult:
    tokens = exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token or not refresh_token:
        raise ValueError("Не удалось получить токены по переданному коду")

    return await bot_manager.start_bot(access_token=access_token, refresh_token=refresh_token)


@router.get("/status", summary="Получить состояние бота", response_model=BotStatus)
async def get_bot_status() -> BotStatus:
    return bot_manager.get_status()


@router.post("/start", summary="Начать авторизацию Twitch", response_model=AuthStartResponse)
async def start_authorization() -> AuthStartResponse:
    auth_url = build_auth_url()
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
        return await _start_bot_with_code(code)
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
