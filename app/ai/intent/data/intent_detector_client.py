from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.intent.domain.intent_detector import IntentDetectorClient
from app.ai.intent.domain.models import Intent

_MODEL_PATH = Path(__file__).resolve().parents[4] / "intent_model"
_CONFIDENCE_THRESHOLD = 0.6


class IntentDetectorClientImpl(IntentDetectorClient):
    _JUNK_KEYWORDS = {
        "лол",
        "кек",
        "рофл",
        "ахах",
        "ебать",
        "сука",
        "пизда",
        "хер",
        "жопа",
        "lul",
        "kek",
    }
    _HELLO_KEYWORDS = {
        "ку",
        "прив",
        "привет",
        "приветствую",
        "салам",
        "хай",
        "здарова",
        "здаров",
        "дарова",
        "hello",
        "heyguys",
    }
    _JACKBOX_KEYWORDS = {"jackbox", "джекбокс"}
    _DANKAR_CUT_KEYWORDS = {"нарезка", "нарезку"}
    _SKUF_FEMBOY_KEYWORDS = {"скуф", "фембой"}

    def __init__(self) -> None:
        tokenizer = AutoTokenizer.from_pretrained(_MODEL_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(_MODEL_PATH)
        model.eval()
        self._tokenizer = tokenizer
        self._model = model
        self._id2label = model.config.id2label

    def extract_intent_from_text(self, text: str) -> Intent:
        rule_based_intent = self._match_rule(text)
        if rule_based_intent is not None:
            return self._to_intent(rule_based_intent)

        inputs = self._tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=64)
        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)
            confidence, prediction = torch.max(probs, dim=1)

        label = self._id2label[prediction.item()]
        if _CONFIDENCE_THRESHOLD > confidence.item():
            label = Intent.OTHER.value
        return self._to_intent(label)

    def _match_rule(self, text: str) -> str | None:
        text_lower = text.lower().strip()
        words = text_lower.split()

        if len(words) <= 2 and any(word in self._JUNK_KEYWORDS for word in words):
            return "junk"

        if any(word in self._JACKBOX_KEYWORDS for word in words):
            return Intent.JACKBOX.value

        if any(word in self._DANKAR_CUT_KEYWORDS for word in words):
            return Intent.DANKAR_CUT.value

        if any(word in self._SKUF_FEMBOY_KEYWORDS for word in words):
            return Intent.SKUF_FEMBOY.value

        if any(word in self._HELLO_KEYWORDS for word in words):
            return Intent.HELLO.value

        return None

    @staticmethod
    def _to_intent(label: str) -> Intent:
        for intent in Intent:
            if intent.value == label:
                return intent
        return Intent.OTHER

    async def validate_intent_via_llm(self, detected_intent: Intent, text: str, llm_repository: LLMRepository) -> Intent:
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
            f'Текст сообщения: "{text}"\n'
            f"Система ранее определила intent как: {detected_intent.value}.\n"
            "Если intent определён верно, просто напиши его (одно слово, без пояснений). "
            "Если определён неверно — напиши правильный intent (одно слово, без пояснений)."
        )
        ai_response = await llm_repository.generate_ai_response([AIMessage(role=Role.USER, content=prompt)])
        ai_message = ai_response.message.strip().lower()
        for intent in Intent:
            if ai_message == intent.value:
                return intent
        return detected_intent
