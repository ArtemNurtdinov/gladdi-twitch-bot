from sqlalchemy import text
from db.base import engine
from features.ai.db.ai_message import AIMessage
from features.battle.db.battle_history import BattleHistory
from features.betting.db.bet_history import BetHistory
from features.chat.db.chat_message import ChatMessage
from features.minigame.db.word_history import WordHistory
from features.economy.db.user_balance import UserBalance
from features.economy.db.transaction_history import TransactionHistory
from features.equipment.db.user_equipment import UserEquipment
from features.stream.db.stream import Stream
from features.stream.db.stream_viewer_session import StreamViewerSession


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
        print("Таблицы успешно созданы!")

        with engine.connect() as connection:
            tables_result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = [row[0] for row in tables_result]
            print(f"Таблицы после создания: {', '.join(tables)}")

    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")


if __name__ == "__main__":
    test_connection()
    create_tables()
