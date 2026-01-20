from app.minigame.application.word_history_uow import WordHistoryUnitOfWorkFactory


class GetUsedWordsUseCase:
    def __init__(self, unit_of_work_factory: WordHistoryUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def get_used_words(self, channel_name: str, limit: int) -> list[str]:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            return uow.word_history_repo.list_recent_words(channel_name, limit)
