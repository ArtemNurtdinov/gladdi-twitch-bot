from config import config
from features.ai.message import AIMessage
import requests
from features.ai.intent import Intent


class AIService:
    _LLMBOX_API_DOMAIN = config.llmbox.host
    _INTENT_DETECTOR_API_DOMAIN = config.intent_detector.host

    def generate_ai_response(self, user_messages: list[AIMessage]) -> str:
        messages = []
        for message in user_messages:
            messages.append({"role": message.role.value, "content": message.content})

        payload = {"messages": messages, "assistant": "chat_gpt"}
        api_url = f"{self._LLMBOX_API_DOMAIN}/generate-ai-response"

        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            response_data = response.json()

            assistant_message = response_data["assistant_message"]
            return assistant_message
        else:
            raise Exception(f"Ошибка запроса: {response.status_code} - {response.text}")

    def extract_intent_from_text(self, text: str) -> Intent:
        api_url = f"{self._INTENT_DETECTOR_API_DOMAIN}/extract-intent"
        payload = {"message": text}

        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            response_data = response.json()

            intent_value = response_data["intent"]

            for intent in Intent:
                if intent.value == intent_value:
                    return intent
            return Intent.OTHER
        else:
            raise Exception(f"Ошибка запроса: {response.status_code} - {response.text}")

    def get_jackbox_prompt(self, source: str, nickname: str, message: str) -> str:
        return (f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}."
                f"\n\n Если вопрос связан с тем, когда будет игра jackbox, то ответь, что никогда не будет и что поднимать эту тему запрещено на этом канале!")

    def get_skuf_femboy_prompt(self, source: str, nickname: str, message: str) -> str:
        return (f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}.\n\nЕсли вопрос связан с тем, кто и на сколько % скуф или фембой, "
                f"то вот дополнительная информация:"
                f"\n@ArtemNeFRiT — 43% скуф, 12% фембой"
                f"\n@d3ar_88 — 28% скуф, 27% фембой"
                f"\n@dankar1000 — 61% скуф, 9% фембой"
                f"\n@Gidrovlad — 47% скуф, 35% фембой"
                f"\n@crazyg1mer — 73% скуф, 62% фембой"
                f"\n@pr9mo_mejdy_bylochek — 37% скуф"
                f"\n@tikva_cheel12 — 34% скуф, 19% фембой"
                f"\n@voidterror — 92% скуф, 24% фембой")

    def get_dankar_cut_prompt(self, source: str, nickname: str, message: str) -> str:
        return (f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}."
                f"\n\nЕсли сообщение связано с просмотром нарезки, то ответь, что поднимать эту тему запрещено на этом канале!")

    def get_hello_prompt(self, source: str, nickname: str, message: str) -> str:
        return (f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}."
                f"\nЕсли сообщение содержит в себе приветствие, поприветствуй его в ответ."
                f"\nЕсли сообщение не содержит приветствие, просто забавно прокомментируй его.")

    def get_default_prompt(self, source: str, nickname: str, message: str) -> str:
        return f"Ответь пользователю {source} с никнеймом {nickname} на его сообщение: {message}."
