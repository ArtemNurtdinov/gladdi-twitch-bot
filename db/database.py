from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import config
from features.stream.db.stream_messages import TwitchMessage
from features.economy.db.user_balance import UserBalance
from features.economy.db.transaction_history import TransactionHistory
from features.equipment.db.user_equipment import UserEquipment
from features.minigame.word.db.word_history import WordHistory

engine = create_engine(config.database.url, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["TwitchMessage", "UserBalance", "TransactionHistory", "UserEquipment", "WordHistory"]
