from app.minigame.domain.repo import WordHistoryRepository


class GetUsedWordsUseCase:

    def __init__(self, repo: WordHistoryRepository):
        self._repo = repo

    def get_used_words(self, channel_name: str, limit: int) -> list[str]:
        words = self._repo.list_recent_words(channel_name, limit)
        return words
