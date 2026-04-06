import json
import logging

from sqlalchemy import select

from app.shop.infrastructure.db.model.shop_item import ShopItem as ShopItemORM
from core.db import get_session_local

logger = logging.getLogger(__name__)


def log_shop_items():
    """Выводит содержимое таблицы shop_items в лог"""
    with get_session_local()() as session:
        stmt = select(ShopItemORM)
        items = session.execute(stmt).scalars().all()

        if not items:
            logger.info("Таблица shop_items пуста")
            return

        logger.info(f"=== Содержимое таблицы shop_items (всего {len(items)} записей) ===")

        for item in items:
            logger.info(
                f"ID: {item.id}, "
                f"Channel: {item.channel_name}, "
                f"Name: {item.name}, "
                f"Price: {item.price}, "
                f"Emoji: {item.emoji}, "
                f"Is Active: {item.is_active}, "
                f"Effects: {json.dumps(item.effects, ensure_ascii=False)}, "
                f"Created: {item.created_at}, "
                f"Updated: {item.updated_at}"
            )

        logger.info("=== Конец списка shop_items ===")


def print_shop_items():
    """Выводит содержимое таблицы shop_items в консоль (без лога)"""
    with get_session_local()() as session:
        stmt = select(ShopItemORM)
        items = session.execute(stmt).scalars().all()

        if not items:
            print("Таблица shop_items пуста")
            return

        print(f"\n=== Содержимое таблицы shop_items (всего {len(items)} записей) ===")

        for item in items:
            print(f"\n--- Item ID: {item.id} ---")
            print(f"  Channel: {item.channel_name}")
            print(f"  Name: {item.name}")
            print(f"  Description: {item.description}")
            print(f"  Price: {item.price}")
            print(f"  Emoji: {item.emoji}")
            print(f"  Is Active: {item.is_active}")
            print(f"  Effects: {json.dumps(item.effects, ensure_ascii=False, indent=2)}")
            print(f"  Created: {item.created_at}")
            print(f"  Updated: {item.updated_at}")

        print("\n=== Конец списка shop_items ===\n")


def print_shop_items_table():
    """Выводит содержимое таблицы shop_items в табличном виде (кратко)"""
    with get_session_local()() as session:
        stmt = select(ShopItemORM)
        items = session.execute(stmt).scalars().all()

        if not items:
            print("Таблица shop_items пуста")
            return

        print(f"\n=== Содержимое таблицы shop_items (всего {len(items)} записей) ===")
        print(f"{'ID':<4} {'Channel':<15} {'Name':<20} {'Price':<8} {'Emoji':<4} {'Active':<6} {'Effects Count':<12}")
        print("-" * 80)

        for item in items:
            effects_count = len(item.effects) if item.effects else 0
            print(
                f"{item.id:<4} {item.channel_name:<15} {item.name:<20} {item.price:<8} {item.emoji:<4} {item.is_active:<6} {effects_count:<12}"
            )

        print("=== Конец списка shop_items ===\n")


# Вызов для проверки
if __name__ == "__main__":
    from app.core.config.di.composition import load_config
    from core.db import init_db

    config = load_config()
    init_db(config.db)

    print_shop_items_table()
    print("\n" + "=" * 50 + "\n")
    print_shop_items()
