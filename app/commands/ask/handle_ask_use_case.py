from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.intent.application.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.gen.domain.prompt_service import PromptService
from app.ai.intent.domain.models import Intent
from app.commands.ask.model import AskCommandDTO
from app.commands.ask.ask_uow import AskUnitOfWorkFactory, AskUnitOfWorkRoFactory


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

    async def handle(self, command_ask: AskCommandDTO) -> str:
        intent = await self._get_intent_from_text_use_case.get_intent_from_text(command_ask.message)

        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(command_ask.display_name, command_ask.message)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self._prompt_service.get_skuf_femboy_prompt(command_ask.display_name, command_ask.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(command_ask.display_name, command_ask.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(command_ask.display_name, command_ask.message)
        else:
            prompt = self._prompt_service.get_default_prompt(command_ask.display_name, command_ask.message)

        with self._unit_of_work_ro_factory.create() as uow:
            history = uow.conversation.get_last_messages(
                channel_name=command_ask.channel_name,
                system_prompt=self._system_prompt
            )

        assistant_message = await self._chat_response_use_case.generate_response_from_history(
            history=history,
            prompt=prompt
        )

        with self._unit_of_work_factory.create() as uow:
            uow.conversation.save_conversation_to_db(
                channel_name=command_ask.channel_name,
                user_message=prompt,
                ai_message=assistant_message
            )
            uow.chat.save_chat_message(
                channel_name=command_ask.channel_name,
                user_name=command_ask.bot_nick.lower(),
                content=assistant_message,
                current_time=command_ask.occurred_at
            )

        return assistant_message
