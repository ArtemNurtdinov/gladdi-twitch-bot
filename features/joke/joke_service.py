from features.joke.settings_manager import SettingsManager
import logging
from typing import Dict, Any


class JokeService:

    def __init__(self, settings_manager: SettingsManager):
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager or SettingsManager()

    def get_jokes_status(self) -> Dict[str, Any]:
        try:
            enabled = self.settings_manager.get_jokes_enabled()
            interval_min, interval_max = self.settings_manager.get_jokes_interval()
            next_joke_info = self.settings_manager.get_next_joke_info()

            self.logger.debug(f"Получен статус анекдотов: enabled={enabled}, interval={interval_min}-{interval_max}")

            return {
                "enabled": enabled,
                "ready": True,
                "message": f"Анекдоты {'включены' if enabled else 'отключены'}",
                "interval": {
                    "min_minutes": interval_min,
                    "max_minutes": interval_max,
                    "description": f"Интервал: {interval_min}-{interval_max} минут"
                },
                "next_joke": next_joke_info
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса анекдотов: {e}")
            return {
                "enabled": False,
                "ready": False,
                "message": f"Ошибка получения статуса: {str(e)}",
                "interval": {
                    "min_minutes": 30,
                    "max_minutes": 60,
                    "description": "Интервал: 30-60 минут (по умолчанию)"
                },
                "next_joke": {
                    "enabled": False,
                    "next_joke_time": None,
                    "minutes_until_next": None,
                    "can_generate_now": False
                }
            }

    def enable_jokes(self) -> Dict[str, Any]:
        try:
            success = self.settings_manager.set_jokes_enabled(True)

            if success:
                self.logger.info("Анекдоты включены через API")
                return {
                    "success": True,
                    "enabled": True,
                    "message": "Анекдоты включены"
                }
            else:
                self.logger.warning("Не удалось включить анекдоты - ошибка сохранения")
                return {
                    "success": False,
                    "enabled": False,
                    "message": "Ошибка сохранения настроек"
                }
        except Exception as e:
            self.logger.error(f"Ошибка включения анекдотов: {e}")
            return {
                "success": False,
                "enabled": False,
                "message": f"Ошибка включения анекдотов: {str(e)}"
            }

    def disable_jokes(self) -> Dict[str, Any]:
        try:
            success = self.settings_manager.set_jokes_enabled(False)

            if success:
                self.logger.info("Анекдоты отключены через API")
                return {
                    "success": True,
                    "enabled": False,
                    "message": "Анекдоты отключены"
                }
            else:
                self.logger.warning("Не удалось отключить анекдоты - ошибка сохранения")
                return {
                    "success": False,
                    "enabled": True,
                    "message": "Ошибка сохранения настроек"
                }
        except Exception as e:
            self.logger.error(f"Ошибка отключения анекдотов: {e}")
            return {
                "success": False,
                "enabled": True,
                "message": f"Ошибка отключения анекдотов: {str(e)}"
            }

    def get_jokes_interval(self) -> Dict[str, Any]:
        try:
            interval_min, interval_max = self.settings_manager.get_jokes_interval()
            next_joke_info = self.settings_manager.get_next_joke_info()

            self.logger.debug(f"Получен интервал анекдотов: {interval_min}-{interval_max} минут")

            return {
                "min_minutes": interval_min,
                "max_minutes": interval_max,
                "description": f"Интервал генерации: {interval_min}-{interval_max} минут",
                "next_joke": next_joke_info
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения интервала анекдотов: {e}")
            return {
                "min_minutes": 30,
                "max_minutes": 60,
                "description": f"Ошибка получения интервала: {str(e)}",
                "next_joke": {
                    "enabled": False,
                    "next_joke_time": None,
                    "minutes_until_next": None,
                    "can_generate_now": False
                }
            }

    def set_jokes_interval(self, interval_min: int, interval_max: int) -> Dict[str, Any]:
        try:
            success = self.settings_manager.set_jokes_interval(interval_min, interval_max)

            if success:
                current_min, current_max = self.settings_manager.get_jokes_interval()
                next_joke_info = self.settings_manager.get_next_joke_info()

                self.logger.info(f"Интервал анекдотов обновлен: {interval_min}-{interval_max} минут")

                return {
                    "success": True,
                    "min_minutes": current_min,
                    "max_minutes": current_max,
                    "description": f"Интервал обновлен: {current_min}-{current_max} минут",
                    "next_joke": next_joke_info
                }
            else:
                self.logger.warning("Не удалось обновить интервал анекдотов - ошибка сохранения")
                return {
                    "success": False,
                    "min_minutes": 30,
                    "max_minutes": 60,
                    "description": "Ошибка сохранения настроек интервала",
                    "next_joke": {
                        "enabled": False,
                        "next_joke_time": None,
                        "minutes_until_next": None,
                        "can_generate_now": False
                    }
                }
        except ValueError as e:
            self.logger.error(f"Ошибка валидации интервала: {e}")
            return {
                "success": False,
                "min_minutes": 30,
                "max_minutes": 60,
                "description": f"Ошибка валидации: {str(e)}",
                "next_joke": {
                    "enabled": False,
                    "next_joke_time": None,
                    "minutes_until_next": None,
                    "can_generate_now": False
                }
            }
        except Exception as e:
            self.logger.error(f"Ошибка установки интервала анекдотов: {e}")
            return {
                "success": False,
                "min_minutes": 30,
                "max_minutes": 60,
                "description": f"Ошибка установки интервала: {str(e)}",
                "next_joke": {
                    "enabled": False,
                    "next_joke_time": None,
                    "minutes_until_next": None,
                    "can_generate_now": False
                }
            }
