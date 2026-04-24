from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.ai.gen.di.container import AIContainer
from app.bot.bot_manager import BotManager
from app.bot.presentation.api.bot_routes import get_bot_manager
from app.bot.presentation.api.model.request.start_bot import StartBotRequest
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.start_bot import AuthStartResponse
from app.chat.presentation.chat_routes import get_logger
from app.core.config.domain.model.application import ApplicationConfig
from app.core.config.domain.model.configuration import Config
from app.core.logger.domain.logger import Logger
from app.economy.di.container import EconomyContainer
from app.follow.di.container import FollowContainer
from app.joke.di.container import JokeContainer
from app.joke.presentation.api.joke_routes import get_joke_container
from app.minigame.di.container import MinigameContainer
from app.platform.auth.di.container import PlatformAuthContainer
from app.shop.di.container import ShopContainer

AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

PERMISSIONS_SCOPE = (
    "chat:read chat:edit "
    "user:read:follows "
    "moderator:read:followers moderator:manage:banned_users moderator:read:chatters "
    "user:read:chat user:write:chat user:bot channel:bot"
)

router = APIRouter()


def get_config(request: Request) -> ApplicationConfig:
    return request.app.state.config


def get_ai_container(request: Request) -> AIContainer:
    return request.app.state.ai_container


def get_shop_container(request: Request) -> ShopContainer:
    return request.app.state.shop_container


def get_minigame_container(request: Request) -> MinigameContainer:
    return request.app.state.minigame_container


def get_economy_container(request: Request) -> EconomyContainer:
    return request.app.state.economy_container


def get_follow_container(request: Request) -> FollowContainer:
    return request.app.state.follow_container


@router.post("/start", summary="Начать авторизацию Twitch", response_model=AuthStartResponse)
async def start_authorization(
    request: StartBotRequest,
    config: Config = Depends(get_config),
) -> AuthStartResponse:
    if not request.channel_name:
        raise HTTPException(status_code=400, detail="Не передан channel_name")
    params = {
        "client_id": config.twitch.client_id,
        "redirect_uri": config.twitch.redirect_url,
        "response_type": "code",
        "scope": PERMISSIONS_SCOPE,
        "state": request.channel_name,
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    return AuthStartResponse(auth_url=auth_url, message="Откройте ссылку, авторизуйтесь — Twitch вернёт вас на redirect_uri")


@router.get(
    "/callback",
    summary="OAuth callback от Twitch: обменивает code и запускает бота",
    response_model=BotActionResultResponse,
)
async def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    bot_manager: BotManager = Depends(get_bot_manager),
    config: Config = Depends(get_config),
    logger: Logger = Depends(get_logger),
    ai_container: AIContainer = Depends(get_ai_container),
    joke_container: JokeContainer = Depends(get_joke_container),
) -> BotActionResultResponse:
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

    platform_auth_container = PlatformAuthContainer(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=config.twitch.client_id,
        client_secret=config.twitch.client_secret,
        logger=logger,
    )

    return await bot_manager.start_bot(
        channel_name=state,
        generate_response_use_case_factory=ai_container.generate_response_use_case_factory,
        conversation_service_factory=ai_container.conversation_service_factory,
        system_prompt_repository_factory=ai_container.system_prompt_repository_factory,
        get_intent_from_text_use_case_factory=ai_container.get_intent_from_text_use_case_factory,
        prompt_service=ai_container.prompt_service,
        llm_repository_factory=ai_container.llm_repository_factory,
        joke_container=joke_container,
        platform_auth=platform_auth_container.platform_auth,
        token_checker_job=platform_auth_container.token_checker_job,
    )


@router.post("/stop", summary="Остановить Twitch бота", response_model=BotActionResultResponse)
async def stop_bot(bot_manager: BotManager = Depends(get_bot_manager)) -> BotActionResultResponse:
    try:
        return await bot_manager.stop_bot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки бота: {e}")
