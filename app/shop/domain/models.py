from typing import Protocol

from app.shop.domain.model.effect import (
    DailyBonusMultiplierEffect,
    MaxBetIncreaseEffect,
    RollCooldownOverrideEffect,
    TimeoutProtectionEffect,
    TimeoutReductionEffect,
)
from app.shop.domain.model.shop_item import ShopItem
from app.shop.domain.model.type import ShopItemType


class ShopItems:
    ITEMS: dict[ShopItemType, ShopItem] = {
        ShopItemType.CHAIR: ShopItem(
            name="стул",
            description="Надёжная опора artemn3STUL",
            price=10000,
            emoji="🪑",
            effects=[
                TimeoutReductionEffect(reduction_factor=0.5, timeout_reduct_message="🪑 Стул обеспечил надёжную опору и снизил таймаут!")
            ],
        ),
        ShopItemType.FREEZER_DUMPLINGS: ShopItem(
            name="пельмени",
            description="Холодная сила сибирских пельменей. Дает бафф к размеру живота",
            price=15000,
            emoji="🥟",
            effects=[DailyBonusMultiplierEffect(multiplier=1.25, message="Нашелся счастливый пельмень, который увеличил бонус!")],
        ),
        ShopItemType.MAEL_EXPEDITION: ShopItem(
            name="маэль",
            description="Умеет рисовать, может перерисовывать судьбы и жизни.",
            price=33333,
            emoji="⚔️",
            effects=[
                DailyBonusMultiplierEffect(multiplier=2, message="Маэль перерисовала судьбу и увеличила бонус! Алиииинаааа аииииии..."),
                TimeoutProtectionEffect(timeout_protect_message="⚔️ Маэль перерисовала судьбу и спасла от таймаута! Алиииинаааа аииииии..."),
            ],
        ),
        ShopItemType.GAMBLER_AMULET: ShopItem(
            name="амулет лудомана",
            description="Снимает ограничения на ставки",
            price=66666,
            emoji="🎰",
            effects=[
                DailyBonusMultiplierEffect(multiplier=3.0, message="Амулет лудомана увеличил бонус!"),
                TimeoutProtectionEffect(timeout_protect_message="🎰 Амулет лудомана защитил от таймаута!"),
                RollCooldownOverrideEffect(cooldown_seconds=5),
                MaxBetIncreaseEffect(max_bet_amount=1_000_000),
            ],
        ),
    }

    @classmethod
    def get_item(cls, item_type: ShopItemType) -> ShopItem:
        return cls.ITEMS[item_type]

    @classmethod
    def get_all_items(cls) -> dict[ShopItemType, ShopItem]:
        return cls.ITEMS.copy()

    @classmethod
    def get_total_items_count(cls) -> int:
        return len(cls.ITEMS)


class OwnedShopItem(Protocol):
    item_type: ShopItemType
    shop_item: ShopItem
