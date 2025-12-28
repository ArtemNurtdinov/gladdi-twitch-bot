from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.intent.application.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.gen.domain.prompt_service import PromptService
from app.ai.intent.domain.models import Intent
from app.twitch.application.interaction.ask.dto import AskCommandDTO
from app.twitch.application.interaction.ask.ask_uow import AskUnitOfWorkFactory, AskUnitOfWorkRoFactory


class HandleAskUseCase:

    def __init__(
        self,
        get_intent_from_text_use_case: GetIntentFromTextUseCase,
        prompt_service: PromptService,
        unit_of_work_factory: AskUnitOfWorkFactory,
        unit_of_work_ro_factory: AskUnitOfWorkRoFactory,
        system_prompt: str,
        chat_response_use_case: ChatResponseUseCase,
    ):
        self._get_intent_from_text_use_case = get_intent_from_text_use_case
        self._prompt_service = prompt_service
        self._unit_of_work_factory = unit_of_work_factory
        self._unit_of_work_ro_factory = unit_of_work_ro_factory
        self._system_prompt = system_prompt
        self._chat_response_use_case = chat_response_use_case

    async def handle(self, dto: AskCommandDTO) -> str:
        intent = await self._get_intent_from_text_use_case.get_intent_from_text(dto.message)

        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(dto.display_name, dto.message)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self._prompt_service.get_skuf_femboy_prompt(dto.display_name, dto.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(dto.display_name, dto.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(dto.display_name, dto.message)
        else:
            prompt = self._prompt_service.get_default_prompt(dto.display_name, dto.message)

        with self._unit_of_work_ro_factory.create() as uow:
            history = uow.conversation.get_last_messages(
                channel_name=dto.channel_name,
                system_prompt=self._system_prompt
            )

        assistant_message = await self._chat_response_use_case.generate_response_from_history(history, prompt)

        with self._unit_of_work_factory.create() as uow:
            uow.conversation.save_conversation_to_db(
                channel_name=dto.channel_name,
                user_message=prompt,
                ai_message=assistant_message
            )
            uow.chat.save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick.lower(),
                content=assistant_message,
                current_time=dto.occurred_at
            )

        return assistant_message
