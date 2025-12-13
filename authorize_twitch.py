import logging
import sys
import webbrowser
from urllib.parse import urlencode
import requests
from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

PERMISSIONS_SCOPE = "chat:read chat:edit user:read:follows moderator:read:followers moderator:manage:banned_users moderator:read:chatters"


def build_auth_url() -> str:
    params = {
        "client_id": config.twitch.client_id,
        "redirect_uri": config.twitch.redirect_url,
        "response_type": "code",
        "scope": PERMISSIONS_SCOPE,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    data = {
        "client_id": config.twitch.client_id,
        "client_secret": config.twitch.client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": config.twitch.redirect_url,
    }
    response = requests.post(TOKEN_URL, data=data, timeout=10)
    if response.status_code != 200:
        logging.error("Не удалось получить токены: %s", response.text)
        raise SystemExit(1)
    return response.json()


def main():
    if not config.twitch.client_id or not config.twitch.client_secret:
        logging.error("Заполните переменные TWITCH_CLIENT_ID и TWITCH_CLIENT_SECRET")
        raise SystemExit(1)

    auth_url = build_auth_url()
    logging.info("Откройте ссылку для авторизации Twitch:")
    logging.info(auth_url)

    try:
        webbrowser.open(auth_url, new=2)
    except Exception:
        logging.warning("Не удалось автоматически открыть браузер, откройте ссылку вручную")

    code = input("Вставьте параметр 'code' из URL после авторизации: ").strip()
    if not code:
        logging.error("Код пустой, авторизация прервана")
        raise SystemExit(1)

    tokens = exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in")

    logging.info("✅ Токены получены")
    logging.info("TWITCH_ACCESS_TOKEN=%s", access_token)
    logging.info("TWITCH_REFRESH_TOKEN=%s", refresh_token)
    logging.info("expires_in: %s секунд", expires_in)
    logging.info("Добавьте значения в переменные TWITCH_ACCESS_TOKEN и TWITCH_REFRESH_TOKEN для Docker.")


if __name__ == "__main__":
    main()
