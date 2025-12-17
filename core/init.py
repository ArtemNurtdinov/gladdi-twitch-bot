from sqlalchemy import text
from core.db import engine, db_session, SessionLocal
from features.ai.db.ai_message import AIMessage
from features.auth.auth_schemas import UserCreate
from features.auth.auth_service import AuthService
from features.auth.db.access_token import AccessToken
from features.auth.db.user import User, UserRole
from features.battle.db.battle_history import BattleHistory
from features.betting.db.bet_history import BetHistory
from features.chat.db.chat_message import ChatMessage
from features.minigame.db.word_history import WordHistory
from features.economy.db.user_balance import UserBalance
from features.economy.db.transaction_history import TransactionHistory
from features.equipment.db.user_equipment import UserEquipment
from features.stream.db.stream import Stream
from features.viewer.db.viewer_session import StreamViewerSession


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"Подключение успешно! Версия PostgreSQL: {version}")

            tables_result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = [row[0] for row in tables_result]

            if tables:
                print(f"Найденные таблицы в базе данных: {', '.join(tables)}")
            else:
                print("В базе данных нет таблиц.")

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")


def create_tables():
    try:
        with engine.begin() as connection:
            AIMessage.__table__.create(bind=connection, checkfirst=True)
            ChatMessage.__table__.create(bind=connection, checkfirst=True)
            BattleHistory.__table__.create(bind=connection, checkfirst=True)
            BetHistory.__table__.create(bind=connection, checkfirst=True)
            UserBalance.__table__.create(bind=connection, checkfirst=True)
            TransactionHistory.__table__.create(bind=connection, checkfirst=True)
            UserEquipment.__table__.create(bind=connection, checkfirst=True)
            Stream.__table__.create(bind=connection, checkfirst=True)
            StreamViewerSession.__table__.create(bind=connection, checkfirst=True)
            WordHistory.__table__.create(bind=connection, checkfirst=True)
            User.__table__.create(bind=connection, checkfirst=True)
            AccessToken.__table__.create(bind=connection, checkfirst=True)
        print("Таблицы успешно созданы!")

        with engine.connect() as connection:
            tables_result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = [row[0] for row in tables_result]
            print(f"Таблицы после создания: {', '.join(tables)}")

    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")


def create_admin():
    try:
        auth_service = AuthService()
        with db_session() as db:
            existing_user = auth_service.get_user_by_email(db, "artem.nefrit@gmail.com")
        if existing_user:
            print(f"   Пользователь с email 'artem.nefrit@gmail.com' уже существует!")
            print(f"   ID: {existing_user.id}")
            print(f"   Роль: {existing_user.role.value}")
            return existing_user

        user_data = UserCreate(
            email="artem.nefrit@gmail.com",
            first_name="Артем",
            last_name="Нуртдинов",
            password="12345",
            role=UserRole.ADMIN,
            is_active=True
        )

        with SessionLocal.begin() as db:
            user = auth_service.create_user_from_admin(db, user_data)
            db.refresh(user)

        print("    Администратор успешно создан!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Имя: {user.first_name} {user.last_name}")
        print(f"   Роль: {user.role.value}")
        print(f"   Активен: {user.is_active}")
        print(f"   Создан: {user.created_at}")

        return user

    except Exception as e:
        print(f"Ошибка создания администратора: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_connection()
    create_tables()
    create_admin()
