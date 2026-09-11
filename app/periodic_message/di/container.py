from sqlalchemy.orm import Session

from app.common.infrastructure.db.session_scoped_factory import SessionScopedFactory
from app.periodic_message.application.mapper.periodic_message_mapper import PeriodicMessageMapper as PeriodicMessageAppMapper
from app.periodic_message.application.usecase.create_periodic_message_use_case import CreatePeriodicMessageUseCase
from app.periodic_message.application.usecase.delete_periodic_message_use_case import DeletePeriodicMessageUseCase
from app.periodic_message.application.usecase.get_all_periodic_messages_use_case import GetAllPeriodicMessagesUseCase
from app.periodic_message.application.usecase.get_periodic_message_use_case import GetPeriodicMessageUseCase
from app.periodic_message.application.usecase.patch_periodic_message_use_case import PatchPeriodicMessageUseCase
from app.periodic_message.domain.repository import PeriodicMessageRepository
from app.periodic_message.infrastructure.mapper.periodic_message_mapper import PeriodicMessageMapper
from app.periodic_message.infrastructure.repository import PeriodicMessageRepositoryImpl
from app.periodic_message.presentation.api.mapper.periodic_message_schema_mapper import PeriodicMessageSchemaMapper


class PeriodicMessageContainer:
    def __init__(self):
        self._infra_mapper = PeriodicMessageMapper()
        self._app_mapper = PeriodicMessageAppMapper()
        self.schema_mapper = PeriodicMessageSchemaMapper()
        self.periodic_message_repository_factory = SessionScopedFactory(self.periodic_message_repository)

    def periodic_message_repository(self, session: Session) -> PeriodicMessageRepository:
        return PeriodicMessageRepositoryImpl(session, self._infra_mapper)

    def get_all_use_case(self, session: Session) -> GetAllPeriodicMessagesUseCase:
        return GetAllPeriodicMessagesUseCase(self.periodic_message_repository(session), self._app_mapper)

    def create_use_case(self, session: Session) -> CreatePeriodicMessageUseCase:
        return CreatePeriodicMessageUseCase(self.periodic_message_repository(session), self._app_mapper)

    def get_use_case(self, session: Session) -> GetPeriodicMessageUseCase:
        return GetPeriodicMessageUseCase(self.periodic_message_repository(session), self._app_mapper)

    def patch_use_case(self, session: Session) -> PatchPeriodicMessageUseCase:
        return PatchPeriodicMessageUseCase(self.periodic_message_repository(session), self._app_mapper)

    def delete_use_case(self, session: Session) -> DeletePeriodicMessageUseCase:
        return DeletePeriodicMessageUseCase(self.periodic_message_repository(session))
