from app.core.config.application.exception.validation import ConfigurationException
from app.core.config.domain.model.configuration import Config


class ValidateConfigUseCase:
    def validate(self, config: Config) -> None:
        missing: list[str] = []

        if not config.application.host:
            missing.append("HOST")
        if not config.application.port:
            missing.append("PORT")
        if not config.application.auth_secret:
            missing.append("ACCESS_SECRET_KEY")
        if not config.application.auth_secret_algorithm:
            missing.append("ACCESS_SECRET_ALGORITHM")

        if not config.db.url:
            missing.append("DATABASE_URL")

        if not config.telegram.bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not config.telegram.group_id:
            missing.append("TELEGRAM_GROUP_ID")

        if not config.twitch.client_id:
            missing.append("TWITCH_CLIENT_ID")
        if not config.twitch.client_secret:
            missing.append("TWITCH_CLIENT_SECRET")
        if not config.twitch.redirect_url:
            missing.append("TWITCH_REDIRECT_URL")
        if not config.twitch.channel_name:
            missing.append("TWITCH_CHANNEL")

        if not config.llmbox.host:
            missing.append("LLMBOX_DOMAIN")

        if not config.intent_detector.host:
            missing.append("INTENT_DETECTOR_DOMAIN")

        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ConfigurationException(f"Missing required configuration keys: {missing_list}")
