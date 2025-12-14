import json
import os
import threading
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import random
import time


@dataclass
class BotSettings:
    jokes_enabled: bool = False
    jokes_interval_min: int = 30
    jokes_interval_max: int = 60
    last_joke_time: Optional[str] = None
    next_joke_time: Optional[str] = None
    last_updated: Optional[str] = None
    version: str = "1.1"


class SettingsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SettingsManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if not self._initialized:
            self.logger = logging.getLogger(__name__)

            if config_path:
                self.settings_file = config_path
            else:
                default_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'bot_settings.json')
                self.settings_file = os.path.abspath(default_path)

            self._file_lock = threading.Lock()
            self._cache_lock = threading.Lock()
            self._cached_settings: Optional[BotSettings] = None
            self._cache_timestamp: Optional[float] = None
            self._cache_ttl = 30

            self._ensure_settings_file_exists()
            self._initialized = True

    def _ensure_settings_file_exists(self):
        try:
            config_dir = os.path.dirname(self.settings_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                self.logger.info(f"Создана директория для настроек: {config_dir}")

            if not os.path.exists(self.settings_file):
                default_settings = BotSettings()
                self._write_settings_to_file(asdict(default_settings))
                self.logger.info(f"Создан файл настроек: {self.settings_file}")
        except Exception as e:
            self.logger.error(f"Ошибка создания файла настроек: {e}")
            raise

    def _is_cache_valid(self) -> bool:
        if self._cached_settings is None or self._cache_timestamp is None:
            return False

        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def _read_settings_from_file(self) -> Dict[str, Any]:
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)

                if 'jokes_interval_min' not in settings_dict:
                    settings_dict['jokes_interval_min'] = 30
                if 'jokes_interval_max' not in settings_dict:
                    settings_dict['jokes_interval_max'] = 60
                if 'last_joke_time' not in settings_dict:
                    settings_dict['last_joke_time'] = None
                if 'next_joke_time' not in settings_dict:
                    settings_dict['next_joke_time'] = None
                if 'version' not in settings_dict or settings_dict['version'] != "1.1":
                    settings_dict['version'] = "1.1"
                    self._write_settings_to_file(settings_dict)
                    self.logger.info("Настройки обновлены до версии 1.1")

                return settings_dict
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Ошибка чтения настроек: {e}")
            return asdict(BotSettings())

    def _write_settings_to_file(self, settings: Dict[str, Any]):
        with self._file_lock:
            try:
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                self.logger.debug(f"Настройки сохранены в файл: {self.settings_file}")
            except Exception as e:
                self.logger.error(f"Ошибка записи настроек: {e}")
                raise

    def _invalidate_cache(self):
        with self._cache_lock:
            self._cached_settings = None
            self._cache_timestamp = None

    def _calculate_next_joke_time(self, interval_min: int, interval_max: int) -> str:
        interval_minutes = random.randint(interval_min, interval_max)
        next_time = datetime.now() + timedelta(minutes=interval_minutes)
        return next_time.isoformat()

    def get_settings(self) -> BotSettings:
        with self._cache_lock:
            if self._is_cache_valid():
                return self._cached_settings

            settings_dict = self._read_settings_from_file()
            self._cached_settings = BotSettings(**settings_dict)

            import time
            self._cache_timestamp = time.time()

            return self._cached_settings

    def update_settings(self, **kwargs) -> bool:
        try:
            current_settings = self.get_settings()

            if 'jokes_interval_min' in kwargs:
                if not isinstance(kwargs['jokes_interval_min'], int) or kwargs['jokes_interval_min'] < 1 or kwargs['jokes_interval_min'] > 300:
                    raise ValueError(f"jokes_interval_min должен быть в диапазоне 1-300 минут: {kwargs['jokes_interval_min']}")

            if 'jokes_interval_max' in kwargs:
                if not isinstance(kwargs['jokes_interval_max'], int) or kwargs['jokes_interval_max'] < 1 or kwargs['jokes_interval_max'] > 300:
                    raise ValueError(f"jokes_interval_max должен быть в диапазоне 1-300 минут: {kwargs['jokes_interval_max']}")

            interval_min = kwargs.get('jokes_interval_min', current_settings.jokes_interval_min)
            interval_max = kwargs.get('jokes_interval_max', current_settings.jokes_interval_max)

            if interval_min > interval_max:
                raise ValueError(f"Минимальный интервал ({interval_min}) не может быть больше максимального ({interval_max})")

            settings_dict = asdict(current_settings)
            settings_dict.update(kwargs)
            settings_dict['last_updated'] = datetime.now().isoformat()

            if ('jokes_interval_min' in kwargs or 'jokes_interval_max' in kwargs) and settings_dict['jokes_enabled']:
                settings_dict['next_joke_time'] = self._calculate_next_joke_time(interval_min, interval_max)
                self.logger.info(f"Пересчитано время следующего анекдота: {settings_dict['next_joke_time']}")

            updated_settings = BotSettings(**settings_dict)

            self._write_settings_to_file(asdict(updated_settings))
            self._invalidate_cache()
            self.logger.info(f"Настройки обновлены: {kwargs}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка обновления настроек: {e}")
            return False

    def get_jokes_enabled(self) -> bool:
        return self.get_settings().jokes_enabled

    def set_jokes_enabled(self, enabled: bool) -> bool:
        settings = self.get_settings()
        update_params = {'jokes_enabled': enabled}

        if enabled and not settings.jokes_enabled:
            update_params['next_joke_time'] = self._calculate_next_joke_time(settings.jokes_interval_min, settings.jokes_interval_max)
            self.logger.info(f"Анекдоты включены, следующий анекдот запланирован на: {update_params['next_joke_time']}")

        if not enabled:
            update_params['next_joke_time'] = None
            self.logger.info("Анекдоты отключены, планирование очищено")

        return self.update_settings(**update_params)

    def get_jokes_interval(self) -> Tuple[int, int]:
        settings = self.get_settings()
        return settings.jokes_interval_min, settings.jokes_interval_max

    def set_jokes_interval(self, interval_min: int, interval_max: int):
        self.update_settings(jokes_interval_min=interval_min, jokes_interval_max=interval_max)

    def is_time_for_joke(self) -> bool:
        settings = self.get_settings()

        if not settings.jokes_enabled:
            return False

        if not settings.next_joke_time:
            return True

        try:
            next_joke_time = datetime.fromisoformat(settings.next_joke_time)
            return datetime.now() >= next_joke_time
        except ValueError as e:
            self.logger.error(f"Ошибка парсинга времени следующего анекдота: {e}")
            return True

    def should_generate_jokes(self) -> bool:
        return self.get_jokes_enabled() and self.is_time_for_joke()

    def mark_joke_generated(self) -> bool:
        settings = self.get_settings()

        if not settings.jokes_enabled:
            return False

        now = datetime.now().isoformat()
        next_joke_time = self._calculate_next_joke_time(settings.jokes_interval_min, settings.jokes_interval_max)

        success = self.update_settings(last_joke_time=now, next_joke_time=next_joke_time)

        if success:
            self.logger.info(f"Анекдот сгенерирован в {now}, следующий запланирован на {next_joke_time}")

        return success

    def get_next_joke_info(self) -> Dict[str, Any]:
        settings = self.get_settings()

        if not settings.jokes_enabled:
            return {
                "enabled": False,
                "next_joke_time": None,
                "minutes_until_next": None,
                "can_generate_now": False
            }

        can_generate_now = self.is_time_for_joke()
        minutes_until_next = None

        if settings.next_joke_time and not can_generate_now:
            try:
                next_joke_time = datetime.fromisoformat(settings.next_joke_time)
                time_diff = next_joke_time - datetime.now()
                minutes_until_next = max(0, int(time_diff.total_seconds() / 60))
            except ValueError:
                pass

        return {
            "enabled": True,
            "next_joke_time": settings.next_joke_time,
            "minutes_until_next": minutes_until_next,
            "can_generate_now": can_generate_now
        }

    def get_all_settings_dict(self) -> Dict[str, Any]:
        return asdict(self.get_settings())

    def reload_from_file(self):
        self._invalidate_cache()
        self.get_settings()
