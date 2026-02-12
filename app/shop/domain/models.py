from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ShopItemType(Enum):
    FREEZER_DUMPLINGS = "freezer_dumplings"
    OCTOPUSES = "octopuses"
    MAEL_EXPEDITION = "mael_expedition"
    COMMUNIST_PARTY = "communist_party"
    BONFIRE = "bonfire"
    CHAIR = "chair"
    GAMBLER_AMULET = "gambler_amulet"


@dataclass
class ItemEffect(ABC):
    pass


@dataclass
class DailyBonusMultiplierEffect(ItemEffect):
    multiplier: float


@dataclass
class TimeoutProtectionEffect(ItemEffect):
    pass


@dataclass
class TimeoutReductionEffect(ItemEffect):
    reduction_factor: float


@dataclass
class RollCooldownOverrideEffect(ItemEffect):
    cooldown_seconds: int


@dataclass
class JackpotPayoutMultiplierEffect(ItemEffect):
    multiplier: float


@dataclass
class PartialPayoutMultiplierEffect(ItemEffect):
    multiplier: float


@dataclass
class MissPayoutMultiplierEffect(ItemEffect):
    multiplier: float


@dataclass
class ShopItem:
    name: str
    description: str
    price: int
    emoji: str
    effects: list[ItemEffect]


class ShopItems:
    ITEMS: dict[ShopItemType, ShopItem] = {
        ShopItemType.FREEZER_DUMPLINGS: ShopItem(
            name="холодильник замороженных пельменей",
            description="Холодная сила сибирских пельменей. Дает бафф к размеру живота",
            price=18000,
            emoji="🥟",
            effects=[DailyBonusMultiplierEffect(multiplier=1.25)],
        ),
        ShopItemType.CHAIR: ShopItem(
            name="стул",
            description="Надёжная опора artemn3STUL",
            price=25000,
            emoji="🪑",
            effects=[TimeoutReductionEffect(reduction_factor=0.5)],
        ),
        ShopItemType.MAEL_EXPEDITION: ShopItem(
            name="маэль из expedition 33",
            description='Умеет рисовать, может перерисовывать судьбы и жизни. Фоном играет песня "Алиииинаааа аииииии"',
            price=33333,
            emoji="⚔️",
            effects=[DailyBonusMultiplierEffect(multiplier=2), TimeoutProtectionEffect()],
        ),
        ShopItemType.GAMBLER_AMULET: ShopItem(
            name="амулет лудомана",
            description="Снимает ограничения на ставки",
            price=66666,
            emoji="🎰",
            effects=[DailyBonusMultiplierEffect(multiplier=3.0), TimeoutProtectionEffect(), RollCooldownOverrideEffect(cooldown_seconds=5)],
        ),
    }

    @classmethod
    def get_item(cls, item_type: ShopItemType) -> ShopItem:
        return cls.ITEMS[item_type]

    @classmethod
    def get_all_items(cls) -> dict[ShopItemType, ShopItem]:
        return cls.ITEMS.copy()

    @classmethod
    def find_item_by_name(cls, name: str) -> ShopItemType:
        name_lower = name.lower().strip()
        for item_type, item in cls.ITEMS.items():
            if item.name.lower() == name_lower:
                return item_type
        raise ValueError(f"Предмет '{name}' не найден")

    @classmethod
    def get_total_items_count(cls) -> int:
        return len(cls.ITEMS)


class OwnedShopItem(Protocol):
    item_type: ShopItemType
    shop_item: ShopItem
