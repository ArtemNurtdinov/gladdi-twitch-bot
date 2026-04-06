from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.core.config.di.composition import load_config
from app.shop.domain.model.shop_item import ShopItemCreate
from app.shop.domain.models import ShopItems
from app.shop.infrastructure.db.model.shop_item import ShopItem as ShopItemORM
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper
from app.shop.infrastructure.repository import ShopItemRepositoryImpl
from core.db import Base, get_session_local, init_db


def run_migration():
    config = load_config()
    init_db(config.db)

    with get_session_local()() as session:  # Убрали async with, используем синхронный with
        mapper = ShopItemMapper()
        repo = ShopItemRepositoryImpl(session, mapper)

        inspector = inspect(session.bind)

        # 1. Создаём таблицу shop_items
        if not inspector.has_table("shop_items"):
            print("📦 Создаём таблицу shop_items...")
            Base.metadata.create_all(session.bind, tables=[ShopItemORM.__table__])
            print("✅ Таблица shop_items создана")
        else:
            print("⚠️ Таблица shop_items уже существует")

        # 2. Заполняем предметами из хардкода
        print("📝 Заполняем предметами...")

        default_channel_name = "artemnefrit"  # Используем твой channel_name

        for item_type, shop_item in ShopItems.ITEMS.items():
            existing = repo.get_active_item_by_name(shop_item.name)

            if not existing:
                shop_item_create = ShopItemCreate(
                    channel_name=default_channel_name,
                    name=shop_item.name,
                    description=shop_item.description,
                    price=shop_item.price,
                    emoji=shop_item.emoji,
                    effects=shop_item.effects,
                )
                added_item = repo.create_item(shop_item_create, is_active=True)
                print(f"  ✅ Добавлен предмет: {added_item.name} (id={added_item.id}) для канала {default_channel_name}")
            else:
                print(f"  ⏭️ Предмет уже существует: {existing.name} (id={existing.id})")

        # 3. Добавляем колонку shop_item_id в user_equipment
        try:
            result = session.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_equipment' AND column_name = 'shop_item_id'
                """)
            )
            column_exists = result.fetchone()

            if not column_exists:
                session.execute(text("ALTER TABLE user_equipment ADD COLUMN shop_item_id INTEGER"))
                print("✅ Добавлена колонка shop_item_id")
            else:
                print("⚠️ Колонка shop_item_id уже существует")
        except OperationalError as e:
            print(f"❌ Ошибка при добавлении колонки: {e}")
            raise

        # 4. Переносим данные из item_type в shop_item_id
        print("🔄 Переносим данные...")

        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_equipment' AND column_name = 'item_type'
            """)
        )
        item_type_exists = result.fetchone()

        if item_type_exists:
            type_to_name = {
                "CHAIR": "стул",
                "FREEZER_DUMPLINGS": "пельмени",
                "MAEL_EXPEDITION": "маэль",
                "GAMBLER_AMULET": "амулет лудомана",
            }

            for old_type, item_name in type_to_name.items():
                result = session.execute(
                    text("""
                        UPDATE user_equipment ue
                        SET shop_item_id = (
                            SELECT id FROM shop_items WHERE name = :item_name
                        )
                        WHERE ue.item_type = :old_type
                        AND ue.shop_item_id IS NULL
                    """),
                    {"item_name": item_name, "old_type": old_type},
                )
                print(f"  Обновлено записей для {old_type}: {result.rowcount}")

            # Проверяем, остались ли NULL значения
            result = session.execute(text("SELECT COUNT(*) FROM user_equipment WHERE shop_item_id IS NULL"))
            null_count = result.scalar()

            if null_count > 0:
                print(f"⚠️ Найдено {null_count} записей с NULL shop_item_id")
                print("  Удаляем проблемные записи...")
                session.execute(text("DELETE FROM user_equipment WHERE shop_item_id IS NULL"))
        else:
            print("⚠️ Колонка item_type не существует, пропускаем перенос данных")

        # 5. Делаем колонку NOT NULL (только если нет NULL значений)
        result = session.execute(text("SELECT COUNT(*) FROM user_equipment WHERE shop_item_id IS NULL"))
        null_count = result.scalar()

        if null_count == 0:
            session.execute(text("ALTER TABLE user_equipment ALTER COLUMN shop_item_id SET NOT NULL"))
            print("✅ Колонка shop_item_id теперь NOT NULL")
        else:
            print(f"❌ Невозможно установить NOT NULL: осталось {null_count} записей с NULL")
            raise Exception(f"Cannot set NOT NULL: {null_count} rows have NULL shop_item_id")

        # 6. Добавляем внешний ключ
        try:
            result = session.execute(
                text("""
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = 'user_equipment' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name = 'fk_user_equipment_shop_item_id'
                """)
            )
            fk_exists = result.fetchone()

            if not fk_exists:
                session.execute(
                    text("""
                        ALTER TABLE user_equipment
                        ADD CONSTRAINT fk_user_equipment_shop_item_id
                        FOREIGN KEY (shop_item_id)
                        REFERENCES shop_items(id)
                        ON DELETE CASCADE
                    """)
                )
                print("✅ Добавлен внешний ключ")
            else:
                print("⚠️ Внешний ключ уже существует")
        except OperationalError as e:
            if "already exists" in str(e):
                print("⚠️ Внешний ключ уже существует")
            else:
                print(f"❌ Ошибка при добавлении внешнего ключа: {e}")
                raise

        # 7. Удаляем старую колонку item_type
        if item_type_exists:
            try:
                session.execute(text("ALTER TABLE user_equipment DROP COLUMN item_type"))
                print("✅ Удалена колонка item_type")
            except OperationalError as e:
                if "does not exist" in str(e):
                    print("⚠️ Колонка item_type уже удалена")
                else:
                    print(f"❌ Ошибка при удалении колонки: {e}")
                    raise
        else:
            print("⚠️ Колонка item_type не существует, пропускаем удаление")

        # 8. Удаляем enum тип (для PostgreSQL)
        try:
            result = session.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'shopitemtype'
                    )
                """)
            )
            type_exists = result.scalar()

            if type_exists:
                session.execute(text("DROP TYPE shopitemtype"))
                print("✅ Удалён тип shopitemtype")
            else:
                print("⚠️ Тип shopitemtype не существует")
        except OperationalError as e:
            print(f"⚠️ Не удалось удалить тип shopitemtype: {e}")

        session.commit()
        print("🎉 Миграция успешно завершена!")


if __name__ == "__main__":
    run_migration()
