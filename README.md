# GLaDDi Twitch Bot

Бот/микросервис для Twitch со встроенным дашбордом. Запускает Twitch‑бота, собирает аналитику по активности чата и
отдаёт REST API для просмотра метрик и управления.

## Возможности

- Twitch‑бот с авторизацией по OAuth и базовым AI‑обработчиком сообщений.
- FastAPI дашборд с OpenAPI документацией (`/docs`).
- Отдельные модули для экономики, мини‑игр, ставок, боёв и аналитики стрима.
- Логирование в файл и консоль, поддержка PostgreSQL через SQLAlchemy.

## Быстрый старт

1) Установите Python 3.11+ и зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2) Создайте `.env` в корне (см. ниже) и заполните токены.
3) Запустите сервис:
   ```bash
   python main.py
   ```
4) Проверьте статус: `GET http://localhost:8000/health` (порт настраивается).

### Запуск в Docker

```bash
docker build -t gladdi-twitch-bot .
docker run --env-file .env -p 8000:8000 gladdi-twitch-bot
```

## Переменные окружения

- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` — получите
  на [twitch developers](https://dev.twitch.tv/docs/authentication/register-app)
- `TWITCH_ACCESS_TOKEN`, `TWITCH_REFRESH_TOKEN` — получите, вызвав [authorize_twitch.py](authorize_twitch.py)
- `TWITCH_CHANNEL` — канал, где работает бот
- `DASHBOARD_PORT` — порт API (по умолчанию 8000)
- `TELEGRAM_BOT_TOKEN` — токен телеграм бота (анонсы стрима)
- `DATABASE_URL` — урл базы данных (PostgreSQL)
- `LLMBOX_DOMAIN` — домен LLMBox (см. https://github.com/ArtemNurtdinov/llmbox)
- `INTENT_DETECTOR_DOMAIN` — домен GLaDDi Intent detector (см. https://github.com/ArtemNurtdinov/gladdi-intent-detector)

Пример `.env`:

```env
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
TWITCH_ACCESS_TOKEN=...
TWITCH_REFRESH_TOKEN=...
TWITCH_CHANNEL=your_channel
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

## Структура

- `main.py` — точка входа: поднимает FastAPI и Twitch‑бота.
- `features/` — модули бота (аналитика, игры, экономика, Twitch API и др.).
- `config.py` — чтение переменных окружения, базовая валидация.
- `Dockerfile` — контейнеризация.


