from typing import Protocol, Generic, TypeVar

DB = TypeVar("DB")


class WordHistoryRepository(Protocol, Generic[DB]):

    def list_recent_words(self, db: DB, channel_name: str, limit: int) -> list[str]:
        ...

    def add_word(self, db: DB, channel_name: str, word: str):
        ...
