from __future__ import annotations

from dataclasses import dataclass

from app.ai.bootstrap import AIProviders
from app.battle.bootstrap import BattleProviders
from app.betting.bootstrap import BettingProviders
from app.chat.bootstrap import ChatProviders
from app.economy.bootstrap import EconomyProviders
from app.equipment.bootstrap import EquipmentProviders
from app.follow.bootstrap import FollowProviders
from app.joke.bootstrap import JokeProviders
from app.minigame.bootstrap import MinigameProviders
from app.stream.bootstrap import StreamProviders
from app.user.bootstrap import UserProviders
from app.viewer.bootstrap import ViewerProviders
from bootstrap.telegram_provider import TelegramProviders
from core.bootstrap.background import BackgroundProviders


@dataclass(frozen=True)
class ProvidersBundle:
    ai_providers: AIProviders
    stream_providers: StreamProviders
    chat_providers: ChatProviders
    follow_providers: FollowProviders
    joke_providers: JokeProviders
    user_providers: UserProviders
    viewer_providers: ViewerProviders
    economy_providers: EconomyProviders
    equipment_providers: EquipmentProviders
    minigame_providers: MinigameProviders
    battle_providers: BattleProviders
    betting_providers: BettingProviders
    background_providers: BackgroundProviders
    telegram_providers: TelegramProviders
