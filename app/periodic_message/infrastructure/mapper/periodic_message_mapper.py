from app.periodic_message.domain.model.periodic_message import PeriodicMessage, PeriodicMessageCreate
from app.periodic_message.infrastructure.db.periodic_message import PeriodicMessageRow


class PeriodicMessageMapper:
    def map_to_domain(self, row: PeriodicMessageRow) -> PeriodicMessage:
        return PeriodicMessage(
            id=row.id,
            channel_name=row.channel_name,
            content=row.content,
            use_llm=row.use_llm,
            interval_minutes=row.interval_minutes,
            is_enabled=row.is_enabled,
            last_sent_at=row.last_sent_at,
            next_send_at=row.next_send_at,
        )

    def map_create_to_db(self, message: PeriodicMessageCreate) -> PeriodicMessageRow:
        return PeriodicMessageRow(
            channel_name=message.channel_name,
            content=message.content,
            use_llm=message.use_llm,
            interval_minutes=message.interval_minutes,
            is_enabled=message.is_enabled,
            last_sent_at=None,
            next_send_at=None,
        )
