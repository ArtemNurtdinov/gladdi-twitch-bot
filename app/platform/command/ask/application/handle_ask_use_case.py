from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.usecases.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.domain.models import Intent
from app.chat.domain.model.chat_message import ChatMessage
from app.platform.command.ask.application.ask_uow import AskUnitOfWorkFactory
from app.platform.command.ask.application.model import AskCommandDTO


class HandleAskUseCase:
    def __init__(
        self,
        get_intent_from_text_use_case: GetIntentFromTextUseCase,
        prompt_service: PromptService,
        unit_of_work_factory: AskUnitOfWorkFactory,
        chat_response_use_case: GenerateResponseUseCase,
    ):
        self._get_intent_from_text_use_case = get_intent_from_text_use_case
        self._prompt_service = prompt_service
        self._unit_of_work_factory = unit_of_work_factory
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
            prompt = self._prompt_service.get_reply_prompt(command_ask.display_name, command_ask.message)

        with self._unit_of_work_factory.create(read_only=True) as uow:
            system_prompt = uow.system_prompt_repository.get_system_prompt(command_ask.channel_name)
            history = uow.conversation_service.get_last_messages(
                channel_name=command_ask.channel_name,
                system_prompt=system_prompt.prompt,
            )

        assistant_message = await self._chat_response_use_case.generate_response_from_history(history=history, prompt=prompt)

        with self._unit_of_work_factory.create() as uow:
            uow.conversation_service.save_conversation_to_db(
                channel_name=command_ask.channel_name,
                user_message=prompt,
                ai_message=assistant_message,
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=command_ask.channel_name,
                    user_name=command_ask.user_name,
                    content=command_ask.message,
                    created_at=command_ask.occurred_at,
                )
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=command_ask.channel_name,
                    user_name=command_ask.bot_nick.lower(),
                    content=assistant_message,
                    created_at=command_ask.occurred_at,
                )
            )

        return assistant_message
