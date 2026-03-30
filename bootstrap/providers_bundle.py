from __future__ import annotations

from dataclasses import dataclass

from app.ai.bootstrap import AIProviders, build_ai_providers
from app.battle.bootstrap import BattleProviders, build_battle_providers
from app.betting.bootstrap import BettingProviders, build_betting_providers
from app.chat.bootstrap import ChatProviders, build_chat_providers
from app.core.logger.domain.logger import Logger
from app.economy.bootstrap import EconomyProviders, build_economy_providers
from app.equipment.bootstrap import EquipmentProviders, build_equipment_providers
from app.follow.bootstrap import FollowProviders, build_follow_providers
from app.minigame.bootstrap import MinigameProviders, build_minigame_providers
from app.stream.bootstrap import StreamProviders, build_stream_providers
from app.viewer.bootstrap import ViewerProviders, build_viewer_providers


@dataclass(frozen=True)
class ProvidersBundle:
    ai_providers: AIProviders
    stream_providers: StreamProviders
    chat_providers: ChatProviders
    follow_providers: FollowProviders
    viewer_providers: ViewerProviders
    economy_providers: EconomyProviders
    equipment_providers: EquipmentProviders
    minigame_providers: MinigameProviders
    battle_providers: BattleProviders
    betting_providers: BettingProviders


def build_providers_bundle(llmbox_host: str, intent_detector_host: str, logger: Logger) -> ProvidersBundle:
    stream_providers = build_stream_providers()
    ai_providers = build_ai_providers(llmbox_host=llmbox_host, intent_detector_host=intent_detector_host)
    chat_providers = build_chat_providers()
    follow_providers = build_follow_providers()
    viewer_providers = build_viewer_providers()
    economy_providers = build_economy_providers()
    equipment_providers = build_equipment_providers()
    minigame_providers = build_minigame_providers(logger=logger)
    battle_providers = build_battle_providers()
    betting_providers = build_betting_providers()

    return ProvidersBundle(
        ai_providers=ai_providers,
        stream_providers=stream_providers,
        chat_providers=chat_providers,
        follow_providers=follow_providers,
        viewer_providers=viewer_providers,
        economy_providers=economy_providers,
        equipment_providers=equipment_providers,
        minigame_providers=minigame_providers,
        battle_providers=battle_providers,
        betting_providers=betting_providers,
    )
