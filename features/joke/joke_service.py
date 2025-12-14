from features.joke.joke_schemas import JokesResponse, JokesIntervalResponse, JokesStatus, JokeInterval
from features.joke.settings_manager import SettingsManager
import logging

logger = logging.getLogger(__name__)


class JokeService:

    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager

    def get_jokes_status(self) -> JokesStatus:
        enabled = self.settings_manager.get_jokes_enabled()
        interval_min, interval_max = self.settings_manager.get_jokes_interval()

        logger.debug(f"Получен статус анекдотов: enabled={enabled}, interval={interval_min}-{interval_max}")

        joke_interval = JokeInterval(
            min_minutes=interval_min,
            max_minutes=interval_max,
            description=f"Интервал: {interval_min}-{interval_max} минут"
        )

        next_joke = self.settings_manager.get_next_joke_info()

        return JokesStatus(enabled=enabled, message=f"Анекдоты {'включены' if enabled else 'отключены'}", interval=joke_interval, next_joke=next_joke)

    def enable_jokes(self) -> JokesResponse:
        try:
            success = self.settings_manager.set_jokes_enabled(True)
            if success:
                logger.info("Анекдоты включены через API")
                return JokesResponse(success=True, message="Анекдоты включены")
            else:
                logger.warning("Не удалось включить анекдоты - ошибка сохранения")
                return JokesResponse(success=False, message="Ошибка сохранения настроек")
        except Exception as e:
            logger.error(f"Ошибка включения анекдотов: {e}")
            return JokesResponse(success=False, message="Ошибка включения анекдотов: {str(e)}")

    def disable_jokes(self) -> JokesResponse:
        try:
            success = self.settings_manager.set_jokes_enabled(False)

            if success:
                logger.info("Анекдоты отключены через API")
                return JokesResponse(success=True, message="Анекдоты отключены")
            else:
                logger.warning("Не удалось отключить анекдоты - ошибка сохранения")
                return JokesResponse(success=False, message="Ошибка сохранения настроек")
        except Exception as e:
            logger.error(f"Ошибка отключения анекдотов: {e}")
            return JokesResponse(success=False, message="Ошибка отключения анекдотов: {str(e)}")

    def set_jokes_interval(self, interval_min: int, interval_max: int) -> JokesIntervalResponse:
        self.settings_manager.set_jokes_interval(interval_min, interval_max)
        current_min, current_max = self.settings_manager.get_jokes_interval()
        next_joke_info = self.settings_manager.get_next_joke_info()

        logger.info(f"Интервал анекдотов обновлен: {interval_min}-{interval_max} минут")
        description = f"Интервал обновлен: {current_min}-{current_max} минут"
        return JokesIntervalResponse(success=True, min_minutes=current_min, max_minutes=current_max, description=description, next_joke=next_joke_info)
