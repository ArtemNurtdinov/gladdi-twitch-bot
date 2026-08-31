from dataclasses import dataclass

from app.ai.gen.di.container import AIContainer
from app.battle.di.container import BattleContainer
from app.betting.di.container import BettingContainer
from app.chat.di.container import ChatContainer
from app.core.config.domain.model.bot import BotConfig
from app.economy.di.container import EconomyContainer
from app.equipment.di.container import EquipmentContainer
from app.platform.command.ask.di.container import AskContainer
from app.platform.di.container import PlatformContainer
from app.shop.di.container import ShopContainer
from app.stream.di.container import StreamContainer


@dataclass(frozen=True)
class CommandRegistryDeps:
    bot: BotConfig
    platform: PlatformContainer
    chat: ChatContainer
    ai: AIContainer
    ask: AskContainer
    battle: BattleContainer
    economy: EconomyContainer
    equipment: EquipmentContainer
    betting: BettingContainer
    stream: StreamContainer
    shop: ShopContainer
