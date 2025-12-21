from datetime import datetime

from sqlalchemy.orm import Session

from app.minigame.domain.repo import WordHistoryRepository
from app.minigame.data.db.word_history import WordHistory as OrmWordHistory


class WordHistoryRepositoryImpl(WordHistoryRepository[Session]):

    def list_recent_words(self, db: Session, channel_name: str, limit: int) -> list[str]:
        rows = (
            db.query(OrmWordHistory.word)
            .filter(OrmWordHistory.channel_name == channel_name)
            .order_by(OrmWordHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [row[0].lower() for row in rows]

    def add_word(self, db: Session, channel_name: str, word: str):
        normalized = "".join(ch for ch in str(word).lower() if ch.isalpha())
        if not normalized:
            return
        record = OrmWordHistory(channel_name=channel_name, word=normalized, created_at=datetime.utcnow())
        db.add(record)

