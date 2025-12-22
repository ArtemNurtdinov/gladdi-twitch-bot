from typing import Protocol


class WordHistoryRepository(Protocol):

    def list_recent_words(self, channel_name: str, limit: int) -> list[str]:
        ...

    def add_word(self, channel_name: str, word: str):
        ...
