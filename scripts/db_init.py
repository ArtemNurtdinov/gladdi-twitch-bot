from sqlalchemy import text

from app.ai.gen.conversation.infrastructure.db.ai_message import AIMessage
from app.auth.application.auth_service import AuthService
from app.auth.domain.models import UserCreateData, UserRole
from app.auth.infrastructure.auth_repository import AuthRepositoryImpl
from app.auth.infrastructure.db.access_token import AccessToken
from app.auth.infrastructure.db.user import User
from app.auth.infrastructure.jwt_token_service import JwtTokenService
from app.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.battle.infrastructure.db.battle_history import BattleHistory
from app.betting.data.db.bet_history import BetHistory
from app.chat.infrastructure.db.chat_message import ChatMessage
from app.economy.data.db.transaction_history import TransactionHistory
from app.economy.data.db.user_balance import UserBalance
from app.equipment.infrastructure.db.user_equipment import UserEquipment
from app.follow.infrastructure.db.follower import ChannelFollowerRow
from app.minigame.infrastructure.db.word_history import WordHistory
from app.stream.infrastructure.db.stream import Stream
from app.viewer.infrastructure.db.viewer_session import StreamViewerSession
from bootstrap.config_provider import get_config
from core.db import db_ro_session, db_rw_session, get_engine


def test_connection():
    try:
        with get_engine().connect() as connection:
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
        with get_engine().begin() as connection:
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
            ChannelFollowerRow.__table__.create(bind=connection, checkfirst=True)
        print("Таблицы успешно созданы!")

        with get_engine().connect() as connection:
            tables_result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = [row[0] for row in tables_result]
            print(f"Таблицы после создания: {', '.join(tables)}")

    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")


def create_admin():
    try:
        config = get_config()
        token_service = JwtTokenService(
            secret=config.application.auth_secret,
            algorithm=config.application.auth_secret_algorithm,
            access_token_expires_minutes=config.application.access_token_expire_minutes,
        )
        password_hasher = BcryptPasswordHasher()
        with db_ro_session() as db:
            auth_service = AuthService(
                repo=AuthRepositoryImpl(db),
                password_hasher=password_hasher,
                token_service=token_service,
            )
            existing_user = auth_service.get_user_by_email("artem.nefrit@gmail.com")
            if existing_user:
                print("   Пользователь с email 'artem.nefrit@gmail.com' уже существует!")
                print(f"   ID: {existing_user.id}")
                print(f"   Роль: {existing_user.role.value}")
                return

        user_data = UserCreateData(
            email="artem.nefrit@gmail.com", first_name="Артем", last_name="Нуртдинов", password="12345", role=UserRole.ADMIN, is_active=True
        )

        with db_rw_session() as db:
            auth_service = AuthService(
                repo=AuthRepositoryImpl(db),
                password_hasher=password_hasher,
                token_service=token_service,
            )
            user = auth_service.create_user_from_admin(user_data)
            print("    Администратор успешно создан!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Имя: {user.first_name} {user.last_name}")
            print(f"   Роль: {user.role.value}")
            print(f"   Активен: {user.is_active}")
            print(f"   Создан: {user.created_at}")

    except Exception as e:
        print(f"Ошибка создания администратора: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_connection()
    create_tables()
    create_admin()
