from enum import StrEnum


class AIAssistant(StrEnum):
    CHAT_GPT = "chat_gpt"
    YANDEX_GPT = "yandex_gpt"
    GPT_OSS_120B = "gpt_oss_120b"
    GPT_OSS_20B = "gpt_oss_20b"
    QWEN3_235B = "qwen3_235b"
