class LLMClientError(Exception):
    """Базовая ошибка LLM клиента."""


class LLMResponseFormatError(LLMClientError):
    """Ошибка формата ответа провайдера LLM."""
