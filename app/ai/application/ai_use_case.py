from app.ai.domain.intent_detector import IntentDetectorClient
from app.ai.domain.llm_client import LLMClient
from app.ai.domain.message_repository import AIMessageRepository
from app.ai.domain.models import AIMessage, Intent


class AIUseCase:

    def __init__(self, llm_client: LLMClient, intent_detector: IntentDetectorClient, message_repo: AIMessageRepository):
        self._llm_client = llm_client
        self._intent_detector = intent_detector
        self._message_repo = message_repo

    def generate_ai_response(self, user_messages: list[AIMessage]) -> str:
        return self._llm_client.generate_ai_response(user_messages)

    def get_intent_from_text(self, text: str) -> Intent:
        detected_intent = self._intent_detector.extract_intent_from_text(text)
        if detected_intent == Intent.HELLO or detected_intent == Intent.DANKAR_CUT or detected_intent == Intent.JACKBOX:
            return self._intent_detector.validate_intent_via_llm(detected_intent, text, self._llm_client)
        else:
            return detected_intent

    def get_jackbox_prompt(self, source: str, nickname: str, message: str) -> str:
        return (
            f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}."
            f"\n\n Если вопрос связан с тем, когда будет игра jackbox, "
            f"то ответь, что никогда не будет и что поднимать эту тему запрещено на этом канале!"
        )

    def get_skuf_femboy_prompt(self, source: str, nickname: str, message: str) -> str:
        return (
            f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}.\n\nЕсли вопрос связан с тем, кто и на сколько % скуф или фембой, "
            f"то вот дополнительная информация:"
            f"\n@ArtemNeFRiT — 43% скуф, 12% фембой"
            f"\n@d3ar_88 — 28% скуф, 27% фембой"
            f"\n@dankar1000 — 61% скуф, 9% фембой"
            f"\n@Gidrovlad — 47% скуф, 35% фембой"
            f"\n@crazyg1mer — 73% скуф, 62% фембой"
            f"\n@pr9mo_mejdy_bylochek — 37% скуф"
            f"\n@tikva_cheel12 — 34% скуф, 19% фембой"
            f"\n@voidterror — 92% скуф, 24% фембой"
        )

    def get_dankar_cut_prompt(self, source: str, nickname: str, message: str) -> str:
        return (f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}."
                f"\n\nЕсли сообщение связано с просмотром нарезки, то ответь, что поднимать эту тему запрещено на этом канале!")

    def get_hello_prompt(self, source: str, nickname: str, message: str) -> str:
        return (f"Сообщение от пользователя {source} с никнеймом {nickname}: {message}."
                f"\nЕсли сообщение содержит в себе приветствие, поприветствуй его в ответ."
                f"\nЕсли сообщение не содержит приветствие, просто забавно прокомментируй его.")

    def get_default_prompt(self, source: str, nickname: str, message: str) -> str:
        return f"Ответь пользователю {source} с никнеймом {nickname} на его сообщение: {message}."

    def get_last_messages(self, channel_name: str, system_prompt: str) -> list[AIMessage]:
        return self._message_repo.get_last_messages(channel_name, system_prompt)

    def save_conversation_to_db(self, channel_name: str, user_message: str, ai_message: str):
        self._message_repo.add_messages_to_db(channel_name, user_message, ai_message)