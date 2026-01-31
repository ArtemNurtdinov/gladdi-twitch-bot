from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.minigame.domain.repo import WordHistoryRepository
from app.minigame.infrastructure.db.word_history import WordHistory as OrmWordHistory


class WordHistoryRepositoryImpl(WordHistoryRepository):
    def __init__(self, db: Session):
        self._db = db

    def list_recent_words(self, channel_name: str, limit: int) -> list[str]:
        stmt = (
            select(OrmWordHistory.word)
            .where(OrmWordHistory.channel_name == channel_name)
            .order_by(OrmWordHistory.created_at.desc())
            .limit(limit)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [word.lower() for word in rows]

    def add_word(self, channel_name: str, word: str):
        record = OrmWordHistory(channel_name=channel_name, word=word, created_at=datetime.utcnow())
        self._db.add(record)
