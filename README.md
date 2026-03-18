# GLaDDi Twitch Bot

Бот для Twitch со встроенной админкой. Запускает Twitch‑бота, собирает аналитику по активности чата и 
предоставляет API для управления и просмотра метрик.

## Возможности

- Twitch‑бот с авторизацией и обработкой сообщений/комманд в чате
- Определение намерения пользователя при помощи ML-модели
- Генерация ответов, анекдотов и мини-игр при помощи LLM
- Автоматическое определение статуса стрима и анонс в телеграмм
- Подведение итогов стрима и суммаризация чата при помощи LLM
- Экономика, мини-игры, ставки, битвы и многое другое

## Команды

Префикс для команд:`!` - устанавливается в [настройках бота](app/platform/bot/model/bot_settings.py)

Быстрый список всех комманд: `!команды`.

- `!баланс` — показать свой баланс
- `!бонус` — получить бонус (один раз за стрим)
- `!ставка [сумма]` — слот‑машина
- `!перевод @ник сумма` — перевод другому пользователю
- `!магазин` — показать товары в магазине
- `!купить <название>` — купить предмет из магазина
- `!экипировка` — показать активные предметы
- `!топ` / `!бомжи` — топ богатых и топ бедных пользователей
- `!стата` — персональная статистика (баланс, ставки, бои)
- `!битва` — встать в очередь на битву или принять вызов в битве
- `!gladdi <текст>` — обратиться к GLaDDi (LLM).
- `!followage` — узнать, сколько вы подписаны на канал.
- Мини‑игры (запускаются во время стрима):
  - `!угадай [число]` — угадать число
  - `!буква <буква>` / `!слово <слово>` — игра «поле чудес»
  - `!кнб <камень/ножницы/бумага>` — подключиться к раунду камень-ножницы-бумага против GLaDDi

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
docker run -d -p 8003:8003 gladdi-twitch-bot
```

## Переменные окружения

- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` — получите
  на [twitch developers](https://dev.twitch.tv/docs/authentication/register-app)
- `TWITCH_REDIRECT_URL` — callback Twitch OAuth
- `TWITCH_CHANNEL` — Twitch канал, к которому подключится бот
- `DASHBOARD_PORT` — порт API (по умолчанию 8003)
- `TELEGRAM_BOT_TOKEN` — токен телеграм бота
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



