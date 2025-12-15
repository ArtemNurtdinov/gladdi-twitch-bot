# GLaDDi Twitch Bot

Бот/микросервис для Twitch со встроенным дашбордом. Запускает Twitch‑бота, собирает аналитику по активности чата и
отдаёт REST API для просмотра метрик и управления.

## Возможности

- Twitch‑бот с авторизацией по OAuth и базовым AI‑обработчиком сообщений.
- FastAPI дашборд с OpenAPI документацией (`/docs`).
- Отдельные модули для экономики, мини‑игр, ставок, боёв и аналитики стрима.
- Логирование в файл и консоль, поддержка PostgreSQL через SQLAlchemy.

## Команды Twitch‑бота

Префикс команд — `!`. Быстрый список в чате: `!команды`.

- `!баланс` — показать баланс.
- `!бонус` — получить бонусные монеты (только во время стрима).
- `!ставка [сумма]` — слот‑машина.
- `!перевод @ник сумма` — отправить монеты другому пользователю.
- `!магазин` — показать артефакты и их цену; `!купить <название>` — купить предмет.
- `!экипировка` — показать активные предметы и дату их истечения.
- `!топ` / `!бомжи` — топ богатых и топ бедных по монетам.
- `!стата` — персональная статистика (баланс, заработок, ставки, бои).
- `!битва` — встать в очередь на дуэль или принять вызов; победитель получает монеты, проигравший — таймаут.
- `!gladdi <текст>` — спросить GLaDDi (AI).
- `!followage` — узнать, сколько вы подписаны на канал.
- Мини‑игры (запускаются автоматически во время стрима):
  - `!угадай [число]` — угадать число; без параметра покажет статус игры.
  - `!буква <буква>` / `!слово <слово>` — игра «поле чудес» (буква или целое слово).
  - `!кнб <камень/ножницы/бумага>` — подключиться к раунду КНБ.

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
4) Проверьте статус: `GET http://localhost:8003/health` (порт настраивается).

### Запуск в Docker

```bash
docker build -t gladdi-twitch-bot .
docker run --env-file .env -p 8003:8003 gladdi-twitch-bot
```

## Переменные окружения

- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` — получите
  на [twitch developers](https://dev.twitch.tv/docs/authentication/register-app)
- `TWITCH_REDIRECT_URL` — callback Twitch OAuth (по умолчанию `http://localhost:8003/api/v1/bot/callback`)
- `TWITCH_CHANNEL` — ваш Twitch канал, к которому подключится бот
- `DASHBOARD_PORT` — порт API (по умолчанию 8003)
- `TELEGRAM_BOT_TOKEN` — токен телеграм бота (анонсы стрима)
- `TELEGRAM_GROUP_ID` — группа для анонсов стрима
- `DATABASE_URL` — урл базы данных (PostgreSQL)
- `LLMBOX_DOMAIN` — домен LLMBox (см. https://github.com/ArtemNurtdinov/llmbox)
- `INTENT_DETECTOR_DOMAIN` — домен GLaDDi Intent detector (см. https://github.com/ArtemNurtdinov/gladdi-intent-detector)

Пример `.env`:

```env
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
TWITCH_REDIRECT_URL=http://localhost:8003/api/v1/bot/callback
TWITCH_CHANNEL=your_channel

TELEGRAM_BOT_TOKEN=123456789:AAAbbbCccDddEeeFffGggHhhIiiJjjKkkL
TELEGRAM_GROUP_ID=-1009876543210

DATABASE_URL=postgresql://user:pass@host:5432/dbname

LLMBOX_DOMAIN=http://llmbox:8000
INTENT_DETECTOR_DOMAIN=http://gladdi-intent-detector:8000
```

## Структура

- `main.py` — точка входа.
- `features/` — модули бота (чат, аналитика, игры, экономика, интеграции и тд.).
- `config.py` — чтение переменных окружения.
- `Dockerfile` — контейнеризация.



