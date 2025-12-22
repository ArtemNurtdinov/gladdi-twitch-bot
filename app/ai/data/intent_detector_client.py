import requests
from core.config import config
from app.ai.domain.intent_detector import IntentDetectorClient
from app.ai.domain.llm_client import LLMClient
from app.ai.domain.models import Intent, AIMessage, Role


class IntentDetectorClientImpl(IntentDetectorClient):
    _INTENT_DETECTOR_API_DOMAIN = config.intent_detector.host

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

        raise Exception(f"Ошибка запроса: {response.status_code} - {response.text}")

    def validate_intent_via_llm(self, detected_intent: Intent, text: str, llm_client: LLMClient) -> Intent:
        intent_descriptions = {
            "games_history": "вопросы о прошедших играх, их истории, результатах и т.п.",
            "jackbox": "вопросы о Jackbox, просьбы поиграть, обсуждение этой игры",
            "skuf_femboy": "вопросы и обсуждения, кто и на сколько процентов скуф или фембой",
            "dankar_cut": "вопросы и обсуждения, связанные с нарезками Dankar",
            "hello": "приветствия, пожелания доброго дня и т.п.",
            "other": "всё, что не подходит ни под один из вышеперечисленных интентов",
        }

        intent_values = [intent.value for intent in Intent]
        intent_list_str = ", ".join(f"{intent}: {intent_descriptions[intent]}" for intent in intent_values)

        prompt = (
            "Ты — классификатор пользовательских сообщений по intent.\n"
            "Вот список возможных intent с их описаниями:\n"
            f"{intent_list_str}\n"
            f"Текст сообщения: \"{text}\"\n"
            f"Система ранее определила intent как: {detected_intent.value}.\n"
            "Если intent определён верно, просто напиши его (одно слово, без пояснений). "
            "Если определён неверно — напиши правильный intent (одно слово, без пояснений)."
        )
        ai_response = llm_client.generate_ai_response([AIMessage(Role.USER, prompt)])
        ai_response = ai_response.strip().lower()
        for intent in Intent:
            if ai_response == intent.value:
                return intent
        return detected_intent

