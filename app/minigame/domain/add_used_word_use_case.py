from app.minigame.domain.repo import WordHistoryRepository


class AddUsedWordsUseCase:

    def __init__(self, repo: WordHistoryRepository):
        self._repo = repo

    def add_used_words(self, channel_name: str, word: str) -> list[str]:
        return self._repo.add_word(channel_name, word)
