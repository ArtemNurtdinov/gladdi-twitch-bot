from dataclasses import dataclass

import telegram
from telegram.request import HTTPXRequest

from app.ai.gen.data.message_repository import ConversationRepositoryImpl
from app.ai.gen.domain.conversation_service import ConversationService
from app.ai.gen.domain.conversation_service_provider import ConversationServiceProvider
from app.ai.gen.domain.llm_client import LLMClient
from app.ai.gen.domain.prompt_service import PromptService
from app.ai.gen.infrastructure.llm_client import LLMClientImpl
from app.ai.intent.application.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.data.intent_detector_client import IntentDetectorClientImpl
from app.battle.application.battle_use_case import BattleUseCase
from app.battle.application.battle_use_case_provider import BattleUseCaseProvider
from app.battle.data.battle_repository import BattleRepositoryImpl
from app.betting.application.betting_service import BettingService
from app.betting.application.betting_service_provider import BettingServiceProvider
from app.betting.data.betting_repository import BettingRepositoryImpl
from app.chat.application.chat_use_case import ChatUseCase
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.economy.data.economy_repository import EconomyRepositoryImpl
from app.economy.domain.economy_service import EconomyService
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.equipment.data.equipment_repository import EquipmentRepositoryImpl
from app.joke.data.settings_repository import FileJokeSettingsRepository
from app.joke.domain.joke_service import JokeService
from app.minigame.application.add_word.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.add_word.add_used_words_use_case_provider import AddUsedWordsUseCaseProvider
from app.minigame.application.get_used_words.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.application.get_used_words.get_used_words_use_case_provider import GetUsedWordsUseCaseProvider
from app.minigame.data.db.word_history_repository import WordHistoryRepositoryImpl
from app.minigame.domain.minigame_service import MinigameService
from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.application.start_stream_use_case_provider import StartStreamUseCaseProvider
from app.stream.application.stream_service_provider import StreamServiceProvider
from app.stream.data.stream_repository import StreamRepositoryImpl
from app.stream.domain.stream_service import StreamService
from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.viewer.application.viewer_service_provider import ViewerServiceProvider
from app.viewer.data.viewer_repository import ViewerRepositoryImpl
from app.viewer.domain.viewer_session_service import ViewerTimeService
from core.background_task_runner import BackgroundTaskRunner
from core.config import config
from core.provider import Provider, SingletonProvider


@dataclass
class BotDependencies:
    twitch_auth: TwitchAuth
    twitch_api_service: TwitchApiService
    llm_client: LLMClient
    intent_detector: IntentDetectorClientImpl
    get_intent_use_case: GetIntentFromTextUseCase
    prompt_service: PromptService
    joke_service: JokeService
    minigame_service: MinigameService
    user_cache: UserCacheService
    background_runner: BackgroundTaskRunner
    telegram_bot: telegram.Bot
    stream_service_provider: StreamServiceProvider
    chat_use_case_provider: ChatUseCaseProvider
    conversation_service_provider: ConversationServiceProvider
    economy_service_provider: Provider[EconomyService]
    start_stream_use_case_provider: StartStreamUseCaseProvider
    viewer_service_provider: ViewerServiceProvider
    battle_use_case_provider: BattleUseCaseProvider
    betting_service_provider: BettingServiceProvider
    get_used_words_use_case_provider: GetUsedWordsUseCaseProvider
    add_used_words_use_case_provider: AddUsedWordsUseCaseProvider
    get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase]
    roll_cooldown_use_case_provider: SingletonProvider[RollCooldownUseCase]
    equipment_exists_use_case_provider: Provider[EquipmentExistsUseCase]
    add_equipment_use_case_provider: Provider[AddEquipmentUseCase]
    calculate_timeout_use_case_provider: SingletonProvider[CalculateTimeoutUseCase]


def build_bot_dependencies(
    twitch_auth: TwitchAuth,
    twitch_api_service: TwitchApiService,
) -> BotDependencies:
    llm_client = LLMClientImpl()
    intent_detector = IntentDetectorClientImpl()
    get_intent_from_text_use_case = GetIntentFromTextUseCase(intent_detector, llm_client)
    prompt_service = PromptService()

    joke_service = JokeService(FileJokeSettingsRepository())
    minigame_service = MinigameService()
    user_cache = UserCacheService(twitch_api_service)
    background_runner = BackgroundTaskRunner()

    http_request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
    telegram_bot = telegram.Bot(token=config.telegram.bot_token, request=http_request)

    def stream_service(db):
        return StreamService(StreamRepositoryImpl(db))

    def chat_use_case(db):
        return ChatUseCase(ChatRepositoryImpl(db))

    def conversation_service(db):
        return ConversationService(ConversationRepositoryImpl(db))

    def economy_service(db):
        return EconomyService(EconomyRepositoryImpl(db))

    def start_stream_use_case(db):
        return StartNewStreamUseCase(StreamRepositoryImpl(db))

    def viewer_service(db):
        return ViewerTimeService(ViewerRepositoryImpl(db))

    def battle_use_case(db):
        return BattleUseCase(BattleRepositoryImpl(db))

    def betting_service(db):
        return BettingService(BettingRepositoryImpl(db))

    def get_used_words_use_case(db):
        return GetUsedWordsUseCase(WordHistoryRepositoryImpl(db))

    def add_used_word_use_case(db):
        return AddUsedWordsUseCase(WordHistoryRepositoryImpl(db))

    def get_user_equipment_use_case(db):
        return GetUserEquipmentUseCase(EquipmentRepositoryImpl(db))

    def roll_use_case():
        return RollCooldownUseCase()

    def equipment_use_case(db):
        return EquipmentExistsUseCase(EquipmentRepositoryImpl(db))

    def add_equipment_use_case(db):
        return AddEquipmentUseCase(EquipmentRepositoryImpl(db))

    def calculate_timeout_use_case():
        return CalculateTimeoutUseCase()

    deps = BotDependencies(
        twitch_auth=twitch_auth,
        twitch_api_service=twitch_api_service,
        llm_client=llm_client,
        intent_detector=intent_detector,
        get_intent_use_case=get_intent_from_text_use_case,
        prompt_service=prompt_service,
        joke_service=joke_service,
        minigame_service=minigame_service,
        user_cache=user_cache,
        background_runner=background_runner,
        telegram_bot=telegram_bot,
        stream_service_provider=StreamServiceProvider(stream_service),
        chat_use_case_provider=ChatUseCaseProvider(chat_use_case),
        conversation_service_provider=ConversationServiceProvider(conversation_service),
        economy_service_provider=Provider(economy_service),
        start_stream_use_case_provider=StartStreamUseCaseProvider(start_stream_use_case),
        viewer_service_provider=ViewerServiceProvider(viewer_service),
        battle_use_case_provider=BattleUseCaseProvider(battle_use_case),
        betting_service_provider=BettingServiceProvider(betting_service),
        get_used_words_use_case_provider=GetUsedWordsUseCaseProvider(get_used_words_use_case),
        add_used_words_use_case_provider=AddUsedWordsUseCaseProvider(add_used_word_use_case),
        get_user_equipment_use_case_provider=Provider(get_user_equipment_use_case),
        roll_cooldown_use_case_provider=SingletonProvider(roll_use_case),
        equipment_exists_use_case_provider=Provider(equipment_use_case),
        add_equipment_use_case_provider=Provider(add_equipment_use_case),
        calculate_timeout_use_case_provider=SingletonProvider(calculate_timeout_use_case)
    )
    return deps
