import asyncio
import logging
import signal
import sys
import uvicorn
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from config import config
from features.dashboard import dashboard_routes
from features.twitch.twitch_bot import Bot as TwitchBot
from features.twitch.auth import TwitchAuth
from features.twitch.api.twitch_api_service import TwitchApiService
from features.twitch.twitch_repository import TwitchService
from features.ai.ai_service import AIService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.logging.file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="GLaDDi Twitch Bot API",
    description="REST API для аналитики активности Twitch и Telegram бота",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_routes.router, prefix="/api/v1", tags=["Analytics"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "GLaDDi Twitch Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "message": "API is running",
        "service": "GLaDDi Twitch Bot"
    }


class ServiceManager:

    def __init__(self):
        self.services = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.dashboard_server = None
        self.twitch_bot = None

    async def start_dashboard(self):
        def run_dashboard():
            try:
                logger.info("Запуск Analytics API GLaDDi Twitch Bot...")
                uvicorn.run("main:app", host=config.dashboard.host, port=config.dashboard.port, log_level=config.dashboard.log_level, reload=False)
            except Exception as e:
                logger.error(f"Ошибка запуска дашборда: {e}")

        self.dashboard_server = self.executor.submit(run_dashboard)
        logger.info("Дашборд запущен")

    async def start_twitch_bot(self):
        try:
            logger.info("Инициализация Twitch бота...")

            auth = TwitchAuth()
            token_ready = False

            if auth.access_token:
                token_ready = auth.check_token_is_valid()

            if not token_ready:
                raise RuntimeError("Twitch токен недействителен. Укажите TWITCH_ACCESS_TOKEN и TWITCH_REFRESH_TOKEN в окружении.")

            ai_repository = AIService()
            twitch_repository = TwitchService(ai_repository)
            twitch_api_service = TwitchApiService(auth)

            self.twitch_bot = TwitchBot(auth, twitch_api_service, twitch_repository, ai_repository)
            await self.twitch_bot.start()
            logger.info("Twitch бот запущен")
        except Exception as e:
            logger.error(f"Ошибка инициализации Twitch бота: {e}")

    async def start_all_services(self):
        self.running = True
        logger.info("Запуск всех сервисов...")

        try:
            await asyncio.gather(self.start_dashboard(), self.start_twitch_bot(), return_exceptions=True)
            logger.info("Все сервисы запущены успешно!")
        except Exception as e:
            logger.error(f"Ошибка при запуске сервисов: {e}")
            await self.shutdown()

    async def shutdown(self):
        if not self.running:
            return

        logger.info("Останавливаем все сервисы...")
        self.running = False

        try:
            if self.twitch_bot:
                logger.info("Останавливаем Twitch бота...")

            self.executor.shutdown(wait=True)
            logger.info("Все сервисы остановлены")
        except Exception as e:
            logger.error(f"Ошибка при остановке сервисов: {e}")


async def main():
    service_manager = ServiceManager()

    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}, начинаем остановку...")
        asyncio.create_task(service_manager.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await service_manager.start_all_services()

        while service_manager.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await service_manager.shutdown()
        logger.info("Приложение завершено")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
