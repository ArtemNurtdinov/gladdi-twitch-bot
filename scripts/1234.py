from sqlalchemy import select, text

from app.core.config.di.composition import load_config
from app.equipment.infrastructure.db.user_equipment import UserEquipment
from app.shop.infrastructure.db.model.shop_item import ShopItem as ShopItemORM
from core.db import get_session_local, init_db


def print_user_equipment():
    """Выводит содержимое таблицы user_equipment в консоль"""
    config = load_config()
    init_db(config.db)

    with get_session_local()() as session:
        # Получаем все записи с JOIN на shop_items для отображения имени предмета
        stmt = (
            select(
                UserEquipment.id,
                UserEquipment.channel_name,
                UserEquipment.user_name,
                UserEquipment.shop_item_id,
                UserEquipment.expires_at,
                UserEquipment.created_at,
                ShopItemORM.name.label("item_name"),
                ShopItemORM.emoji.label("item_emoji"),
                ShopItemORM.price.label("item_price"),
            )
            .join(ShopItemORM, UserEquipment.shop_item_id == ShopItemORM.id)
            .order_by(UserEquipment.created_at.desc())
        )

        items = session.execute(stmt).all()

        if not items:
            print("Таблица user_equipment пуста")
            return

        print(f"\n=== Содержимое таблицы user_equipment (всего {len(items)} записей) ===")
        print(f"{'ID':<6} {'Channel':<15} {'User':<20} {'Item ID':<8} {'Item Name':<20} {'Expires At':<20} {'Created At':<20}")
        print("-" * 110)

        for item in items:
            print(
                f"{item.id:<6} "
                f"{item.channel_name:<15} "
                f"{item.user_name:<20} "
                f"{item.shop_item_id:<8} "
                f"{item.item_emoji} {item.item_name:<18} "
                f"{str(item.expires_at):<20} "
                f"{str(item.created_at):<20}"
            )

        print("=== Конец списка user_equipment ===\n")

        # Дополнительная статистика
        stats_stmt = (
            select(UserEquipment.channel_name, UserEquipment.user_name, text("COUNT(*) as items_count"))
            .group_by(UserEquipment.channel_name, UserEquipment.user_name)
            .order_by(text("items_count DESC"))
        )

        stats = session.execute(stats_stmt).all()

        if stats:
            print("\n=== Статистика по пользователям ===")
            print(f"{'Channel':<15} {'User':<20} {'Items Count':<12}")
            print("-" * 50)
            for stat in stats:
                # Доступ к полям по индексу или по имени
                channel_name = stat[0]  # или stat.channel_name
                user_name = stat[1]  # или stat.user_name
                items_count = stat[2]  # или stat.items_count
                print(f"{channel_name:<15} {user_name:<20} {items_count:<12}")
            print("=== Конец статистики ===\n")


def print_expired_equipment():
    """Выводит просроченные предметы"""
    from datetime import datetime

    config = load_config()
    init_db(config.db)

    with get_session_local()() as session:
        stmt = (
            select(
                UserEquipment.id,
                UserEquipment.channel_name,
                UserEquipment.user_name,
                ShopItemORM.name.label("item_name"),
                UserEquipment.expires_at,
            )
            .join(ShopItemORM, UserEquipment.shop_item_id == ShopItemORM.id)
            .where(UserEquipment.expires_at <= datetime.utcnow())
        )

        expired = session.execute(stmt).all()

        if not expired:
            print("Нет просроченных предметов")
            return

        print(f"\n=== Просроченные предметы (всего {len(expired)}) ===")
        for item in expired:
            print(f"  {item.user_name}: {item.item_name} (истёк {item.expires_at})")
        print("=== Конец списка ===\n")


if __name__ == "__main__":
    print_user_equipment()
    print_expired_equipment()
