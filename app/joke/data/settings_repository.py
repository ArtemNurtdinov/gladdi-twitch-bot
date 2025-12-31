import json
import logging
import os
import threading
import time
from dataclasses import asdict
from typing import Any

from app.joke.domain.models import BotSettings
from app.joke.domain.repo import JokeSettingsRepository


class FileJokeSettingsRepository(JokeSettingsRepository):
    def __init__(self, config_path: str | None = None, cache_ttl: int = 30):
        self.logger = logging.getLogger(__name__)
        default_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "bot_settings.json")
        self.settings_file = os.path.abspath(config_path or default_path)

        self._file_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        self._cached_settings: BotSettings | None = None
        self._cache_timestamp: float | None = None
        self._cache_ttl = cache_ttl

        self._ensure_settings_file_exists()

    def _ensure_settings_file_exists(self) -> None:
        config_dir = os.path.dirname(self.settings_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            self.logger.info("Создана директория для настроек: %s", config_dir)

        if not os.path.exists(self.settings_file):
            default_settings = BotSettings()
            self._write_settings_to_file(asdict(default_settings))
            self.logger.info("Создан файл настроек: %s", self.settings_file)

    def _is_cache_valid(self) -> bool:
        if self._cached_settings is None or self._cache_timestamp is None:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def _read_settings_from_file(self) -> dict[str, Any]:
        try:
            with open(self.settings_file, encoding="utf-8") as f:
                settings_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error("Ошибка чтения настроек: %s", e)
            return asdict(BotSettings())

        if "jokes_interval_min" not in settings_dict:
            settings_dict["jokes_interval_min"] = 30
        if "jokes_interval_max" not in settings_dict:
            settings_dict["jokes_interval_max"] = 60
        if "last_joke_time" not in settings_dict:
            settings_dict["last_joke_time"] = None
        if "next_joke_time" not in settings_dict:
            settings_dict["next_joke_time"] = None
        if "version" not in settings_dict or settings_dict["version"] != "1.1":
            settings_dict["version"] = "1.1"
            self._write_settings_to_file(settings_dict)
            self.logger.info("Настройки обновлены до версии 1.1")

        return settings_dict

    def _write_settings_to_file(self, settings: dict[str, Any]) -> None:
        with self._file_lock:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        self.logger.debug("Настройки сохранены в файл: %s", self.settings_file)

    def _invalidate_cache(self) -> None:
        with self._cache_lock:
            self._cached_settings = None
            self._cache_timestamp = None

    def load(self) -> BotSettings:
        with self._cache_lock:
            if self._is_cache_valid():
                return self._cached_settings

        settings_dict = self._read_settings_from_file()
        loaded = BotSettings(**settings_dict)
        with self._cache_lock:
            self._cached_settings = loaded
            self._cache_timestamp = time.time()
        return loaded

    def save(self, settings: BotSettings) -> BotSettings:
        settings_dict = asdict(settings)
        settings_dict["last_updated"] = settings.last_updated or settings_dict.get("last_updated")
        self._write_settings_to_file(settings_dict)
        with self._cache_lock:
            self._cached_settings = settings
            self._cache_timestamp = time.time()
        return settings

    def reload(self) -> BotSettings:
        self._invalidate_cache()
        return self.load()
