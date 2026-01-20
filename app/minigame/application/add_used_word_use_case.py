from app.minigame.application.word_history_uow import WordHistoryUnitOfWorkFactory


class AddUsedWordsUseCase:
    def __init__(self, unit_of_work_factory: WordHistoryUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def add_used_words(self, channel_name: str, word: str):
        normalized = "".join(ch for ch in str(word).lower() if ch.isalpha())
        if not normalized:
            return
        with self._unit_of_work_factory.create() as uow:
            return uow.word_history_repo.add_word(channel_name, normalized)
