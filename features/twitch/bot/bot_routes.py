from fastapi import APIRouter, HTTPException

from authorize_twitch import build_auth_url, exchange_code_for_tokens
from features.twitch.bot.bot_manager import BotManager
from features.twitch.bot.bot_schemas import AuthCodeRequest, AuthStartResponse, BotActionResult, BotStatus

router = APIRouter(prefix="/bot", tags=["Bot"])

bot_manager = BotManager()


@router.get("/status", summary="Получить состояние бота", response_model=BotStatus)
async def get_bot_status() -> BotStatus:
    return bot_manager.get_status()


@router.post("/start", summary="Начать авторизацию Twitch", response_model=AuthStartResponse)
async def start_authorization() -> AuthStartResponse:
    auth_url = build_auth_url()
    return AuthStartResponse(auth_url=auth_url, message="Откройте ссылку и авторизуйтесь, затем передайте code на эндпоинт /authorize")


@router.post("/authorize", summary="Получить токены по code и запустить бота", response_model=BotActionResult)
async def authorize_and_start(payload: AuthCodeRequest) -> BotActionResult:
    try:
        tokens = exchange_code_for_tokens(payload.code)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token or not refresh_token:
            raise ValueError("Не удалось получить токены по переданному коду")

        return await bot_manager.start_bot(access_token=access_token, refresh_token=refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска бота: {e}")


@router.post("/stop", summary="Остановить Twitch бота", response_model=BotActionResult)
async def stop_bot() -> BotActionResult:
    try:
        return await bot_manager.stop_bot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки бота: {e}")
