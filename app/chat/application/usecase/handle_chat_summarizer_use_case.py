from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.chat.application.model.summarizer_job import SummarizerJobDTO, SummarizerResult
from app.chat.application.uow.chat_summarizer_uow import ChatSummarizerUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.core.logger.domain.logger import Logger
from core.types import SessionFactory


class HandleChatSummarizerUseCase:
    def __init__(
        self,
        chat_summarizer_uow: ChatSummarizerUnitOfWorkFactory,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        prompt_service: PromptService,
        session_ro_factory: SessionFactory,
        logger: Logger,
    ):
        self._chat_summarizer_uow = chat_summarizer_uow
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._prompt_service = prompt_service
        self._session_ro = session_ro_factory
        self._logger = logger.create_child(__name__)

    async def handle(self, summarizer_job: SummarizerJobDTO) -> SummarizerResult:
        with self._chat_summarizer_uow.create(read_only=True) as uow:
            active_stream = uow.stream_repository.get_active_stream(summarizer_job.channel_name)
            if not active_stream:
                return SummarizerResult(None, advance_cursor=False)

            since = summarizer_job.since or active_stream.started_at
            messages = uow.chat_use_case.get_chat_messages(summarizer_job.channel_name, since, summarizer_job.occurred_at)

        if not messages:
            return SummarizerResult(None, advance_cursor=True)

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)

        prompt = self._prompt_service.get_stream_chat_summarize(chat_text)

        self._logger.log_info(f"Суммаризация чата: {prompt}")

        with self._session_ro() as session:
            result = await self._generate_response_use_case_factory.get(session).generate_response(prompt, summarizer_job.channel_name)
        return SummarizerResult(result, advance_cursor=True)
