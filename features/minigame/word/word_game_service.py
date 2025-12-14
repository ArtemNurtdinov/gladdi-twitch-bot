from db.base import SessionLocal
from features.minigame.word.db.word_history import WordHistory


class WordGameService:

    def get_used_words(self, channel_name: str, limit: int) -> list[str]:
        db = SessionLocal()
        try:
            q = db.query(WordHistory.word).filter(WordHistory.channel_name == channel_name).order_by(WordHistory.created_at.desc())
            if limit and limit > 0:
                q = q.limit(limit)
            rows = q.all()
            words = [row[0].lower() for row in rows]
            seen = set()
            unique_in_order = []
            for w in words:
                if w not in seen:
                    seen.add(w)
                    unique_in_order.append(w)
            return unique_in_order
        finally:
            db.close()

    def add_used_word(self, channel_name: str, word: str) -> None:
        normalized = "".join(ch for ch in str(word).lower() if ch.isalpha())
        if not normalized:
            return
        db = SessionLocal()
        try:
            record = WordHistory(channel_name=channel_name, word=normalized)
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
