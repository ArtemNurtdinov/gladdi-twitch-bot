from datetime import datetime

from sqlalchemy.orm import Session

from app.minigame.data.db.word_history import WordHistory as OrmWordHistory
from app.minigame.domain.repo import WordHistoryRepository


class WordHistoryRepositoryImpl(WordHistoryRepository):
    def __init__(self, db: Session):
        self._db = db

    def list_recent_words(self, channel_name: str, limit: int) -> list[str]:
        rows = (
            self._db.query(OrmWordHistory.word)
            .filter(OrmWordHistory.channel_name == channel_name)
            .order_by(OrmWordHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [row[0].lower() for row in rows]

    def add_word(self, channel_name: str, word: str):
        record = OrmWordHistory(channel_name=channel_name, word=word, created_at=datetime.utcnow())
        self._db.add(record)
