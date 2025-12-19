from sqlalchemy.orm import Session
import requests
from config import config
from features.ai.domain.models import AIMessage, Intent, Role
from features.ai.domain.repo import AIRepository
from features.ai.data.db.ai_message import AIMessage as AIDbMessage
from sqlalchemy import case


class AIRepositoryImpl(AIRepository[Session]):
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

    def validate_intent_via_llm(self, detected_intent: Intent, text: str) -> Intent:
        intent_descriptions = {
            "games_history": "вопросы о прошедших играх, их истории, результатах и т.п.",
            "jackbox": "вопросы о Jackbox, просьбы поиграть, обсуждение этой игры",
            "skuf_femboy": "вопросы и обсуждения, кто и на сколько процентов скуф или фембой",
            "dankar_cut": "вопросы и обсуждения, связанные с нарезками Dankar",
            "hello": "приветствия, пожелания доброго дня и т.п.",
            "other": "всё, что не подходит ни под один из вышеперечисленных интентов"
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
        ai_response = self.generate_ai_response([AIMessage(Role.USER, prompt)])
        ai_response = ai_response.strip().lower()
        for intent in Intent:
            if ai_response == intent.value:
                return intent
        return detected_intent

    def get_last_messages(self, db: Session, channel_name: str, system_prompt: str) -> list[AIMessage]:
        role_order = case((AIDbMessage.role == Role.USER, 2), (AIDbMessage.role == Role.ASSISTANT, 1), else_=3)

        messages = (
            db.query(AIDbMessage)
            .filter_by(channel_name=channel_name)
            .filter(AIDbMessage.role != Role.SYSTEM)
            .order_by(AIDbMessage.created_at.desc(), role_order)
            .limit(50)
            .all()
        )
        messages.reverse()
        ai_messages = [AIMessage(Role.SYSTEM, system_prompt)]

        for message in messages:
            ai_messages.append(AIMessage(message.role, message.content))
        return ai_messages

    def add_messages_to_db(self, db: Session, channel_name: str, user_message: str, ai_message: str):
        user_message = AIDbMessage(channel_name=channel_name, role=Role.USER, content=user_message)
        ai_message = AIDbMessage(channel_name=channel_name, role=Role.ASSISTANT, content=ai_message)
        db.add(user_message)
        db.add(ai_message)
