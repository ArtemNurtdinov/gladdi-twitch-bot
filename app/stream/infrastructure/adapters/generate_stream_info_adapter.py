from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.stream.application.port.generate_stream_info_port import GenerateStreamInfoPort


class GenerateStreamInfoAdapter(GenerateStreamInfoPort):
    def __init__(self, use_case: GenerateResponseUseCase):
        self._use_case = use_case

    async def generate(self, prompt: str, channel_name: str) -> str:
        return await self._use_case.generate_response(prompt, channel_name)
