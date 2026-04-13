# GLaDDi Twitch Bot

Бот для Twitch со встроенной админкой. 
Запускает Twitch‑бота, собирает аналитику по активности чата и предоставляет API для управления и просмотра метрик.

## Возможности

- Twitch‑бот с авторизацией и обработкой сообщений и команд в чате
- Определение намерения пользователя при помощи ML-модели (анализ текста)
- Генерация ответов, анекдотов и мини-игр при помощи LLM
- Автоматическое определение статуса стрима и анонс в телеграмм
- Суммаризация чата при помощи LLM, подведение итогов стрима
- Экономика, мини-игры, ставки, битвы и многое другое

## Переменные окружения

- `TELEGRAM_BOT_TOKEN` — токен телеграм бота
- `TELEGRAM_GROUP_ID` — тг-группа (анонс стрима, подведение итогов
- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` — получите
  на [twitch developers](https://dev.twitch.tv/docs/authentication/register-app)
- `TWITCH_REDIRECT_URL` — callback Twitch OAuth
- `DASHBOARD_PORT` — порт API (по умолчанию 8003)
- `DATABASE_URL` — урл базы данных (PostgreSQL)
- `LLMBOX_DOMAIN` — домен LLMBox (см. https://github.com/ArtemNurtdinov/llmbox)
- `INTENT_DETECTOR_DOMAIN` — домен GLaDDi Intent detector (см. https://github.com/ArtemNurtdinov/gladdi-intent-detector)
- `COMMAND_PREFIX` - префикс для команд
- `COMMAND_ROLL` - команда для ставки (слот-машина)
- `COMMAND_FOLLOWAGE` - просмотр времени отслеживания канала
- `COMMAND_ASK` - обратиться напрямую к боту (LLM генерирует ответ)
- `COMMAND_FIGHT` - участие в битве (PVP среди пользователей)
- `COMMAND_BALANCE` - просмотр баланса
- `COMMAND_BONUS` - получение бонуса за просмотр стрима
- `COMMAND_TRANSFER` - перевод монет другому пользователю
- `COMMAND_SHOP` - показать магазин предметов
- `COMMAND_BUY` - покупка предмета
- `COMMAND_EQUIPMENT` - показать экипировку пользователя
- `COMMAND_TOP` - топ пользователей (по балансу)
- `COMMAND_STATS` - персональная статистика (баланс, ставки, бои)
- `COMMAND_GUESS` - угадать число (когда активна игра)
- `COMMAND_GUESS_LETTER` - угадать букву (игра «поле чудес»)
- `COMMAND_GUESS_WORD` - угадать слово (игра «поле чудес»)
- `COMMAND_RPS` - участи в камень-ножницы-бумага
- `COMMAND_HELP` - показать команды в чате

Пример `.env`:

```env
ACCESS_SECRET_KEY=...
ACCESS_SECRET_ALGORITHM=HS256

TELEGRAM_BOT_TOKEN=123456789:AAAbbbCccDddEeeFffGggHhhIiiJjjKkkL
TELEGRAM_GROUP_ID=-1009876543210

TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
TWITCH_REDIRECT_URL=http://localhost:8003/api/v1/bot/callback

HOST=0.0.0.0
PORT=8003

DATABASE_URL=postgresql://user:pass@host:5432/dbname

LLMBOX_DOMAIN=http://127.0.0.1:8001
INTENT_DETECTOR_DOMAIN=http://127.0.0.1:8000

COMMAND_PREFIX=!
COMMAND_ROLL=ставка
COMMAND_FOLLOWAGE=followage
COMMAND_ASK=gladdi
COMMAND_FIGHT=битва
COMMAND_BALANCE=баланс
COMMAND_BONUS=бонус
COMMAND_TRANSFER=перевод
COMMAND_SHOP=магазин
COMMAND_BUY=купить
COMMAND_EQUIPMENT=экипировка
COMMAND_TOP=топ
COMMAND_BOTTOM=бомжи
COMMAND_STATS=стата
COMMAND_GUESS=угадай
COMMAND_GUESS_LETTER=буква
COMMAND_GUESS_WORD=слово
COMMAND_RPS=кнб
COMMAND_HELP=команды
```

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



