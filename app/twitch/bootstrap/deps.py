from dataclasses import dataclass
from typing import Callable

import telegram
from telegram.request import HTTPXRequest

from app.ai.application.conversation_service import ConversationService
from app.ai.application.intent_use_case import IntentUseCase
from app.ai.application.prompt_service import PromptService
from app.ai.data.intent_detector_client import IntentDetectorClientImpl
from app.ai.data.llm_client import LLMClientImpl
from app.ai.data.message_repository import AIMessageRepositoryImpl
from app.battle.application.battle_use_case import BattleUseCase
from app.battle.data.battle_repository import BattleRepositoryImpl
from app.betting.data.betting_repository import BettingRepositoryImpl
from app.betting.domain.betting_service import BettingService
from app.chat.application.chat_use_case import ChatUseCase
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.economy.data.economy_repository import EconomyRepositoryImpl
from app.economy.domain.economy_service import EconomyService
from app.equipment.data.equipment_repository import EquipmentRepositoryImpl
from app.equipment.domain.equipment_service import EquipmentService
from app.joke.data.settings_repository import FileJokeSettingsRepository
from app.joke.domain.joke_service import JokeService
from app.minigame.application.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.data.db.word_history_repository import WordHistoryRepositoryImpl
from app.minigame.domain.minigame_service import MinigameService
from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.data.stream_repository import StreamRepositoryImpl
from app.stream.domain.stream_service import StreamService
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.twitch.presentation.auth import TwitchAuth
from app.viewer.data.viewer_repository import ViewerRepositoryImpl
from app.viewer.domain.viewer_session_service import ViewerTimeService
from core.background_task_runner import BackgroundTaskRunner
from core.config import config


@dataclass
class BotDependencies:
    twitch_auth: TwitchAuth
    twitch_api_service: TwitchApiService
    llm_client: LLMClientImpl
    intent_detector: IntentDetectorClientImpl
    intent_use_case: IntentUseCase
    prompt_service: PromptService
    joke_service: JokeService
    minigame_service: MinigameService
    user_cache: UserCacheService
    background_runner: BackgroundTaskRunner
    telegram_bot: telegram.Bot

    chat_use_case_factory: Callable = ChatUseCase
    battle_use_case_factory: Callable = BattleUseCase
    ai_conversation_use_case_factory: Callable = ConversationService
    betting_service_factory: Callable = BettingService
    economy_service_factory: Callable = EconomyService
    equipment_service_factory: Callable = EquipmentService
    get_used_words_use_case_factory: Callable = GetUsedWordsUseCase
    add_used_word_use_case_factory: Callable = AddUsedWordsUseCase
    stream_service_factory: Callable = StreamService
    start_new_stream_use_case_factory: Callable = StartNewStreamUseCase
    viewer_service_factory: Callable = ViewerTimeService

    def chat_use_case(self, db) -> ChatUseCase:
        return self.chat_use_case_factory(ChatRepositoryImpl(db))

    def battle_use_case(self, db) -> BattleUseCase:
        return self.battle_use_case_factory(BattleRepositoryImpl(db))

    def ai_conversation_use_case(self, db) -> ConversationService:
        repo = AIMessageRepositoryImpl(db)
        return self.ai_conversation_use_case_factory(repo)

    def betting_service(self, db) -> BettingService:
        return self.betting_service_factory(BettingRepositoryImpl(db))

    def economy_service(self, db) -> EconomyService:
        return self.economy_service_factory(EconomyRepositoryImpl(db))

    def equipment_service(self, db) -> EquipmentService:
        return self.equipment_service_factory(EquipmentRepositoryImpl(db))

    def get_used_words_use_case(self, db) -> GetUsedWordsUseCase:
        return self.get_used_words_use_case_factory(WordHistoryRepositoryImpl(db))

    def add_used_word_use_case(self, db) -> AddUsedWordsUseCase:
        return self.add_used_word_use_case_factory(WordHistoryRepositoryImpl(db))

    def stream_service(self, db) -> StreamService:
        return self.stream_service_factory(StreamRepositoryImpl(db))

    def start_new_stream_use_case(self, db) -> StartNewStreamUseCase:
        return self.start_new_stream_use_case_factory(StreamRepositoryImpl(db))

    def viewer_service(self, db) -> ViewerTimeService:
        return self.viewer_service_factory(ViewerRepositoryImpl(db))


def build_bot_dependencies(
    twitch_auth: TwitchAuth,
    twitch_api_service: TwitchApiService,
) -> BotDependencies:
    llm_client = LLMClientImpl()
    intent_detector = IntentDetectorClientImpl()
    intent_use_case = IntentUseCase(intent_detector, llm_client)
    prompt_service = PromptService()

    joke_service = JokeService(FileJokeSettingsRepository())
    minigame_service = MinigameService()
    user_cache = UserCacheService(twitch_api_service)
    background_runner = BackgroundTaskRunner()

    http_request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
    telegram_bot = telegram.Bot(token=config.telegram.bot_token, request=http_request)

    return BotDependencies(
        twitch_auth=twitch_auth,
        twitch_api_service=twitch_api_service,
        llm_client=llm_client,
        intent_detector=intent_detector,
        intent_use_case=intent_use_case,
        prompt_service=prompt_service,
        joke_service=joke_service,
        minigame_service=minigame_service,
        user_cache=user_cache,
        background_runner=background_runner,
        telegram_bot=telegram_bot,
    )

