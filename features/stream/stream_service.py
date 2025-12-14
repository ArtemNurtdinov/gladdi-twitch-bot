import logging
from typing import Optional, List
from datetime import datetime
from db.base import SessionLocal
from features.stream.db.stream import Stream
from features.stream.db.stream_viewer_session import StreamViewerSession

logger = logging.getLogger(__name__)


class StreamService:

    def __init__(self):
        pass
    
    def create_stream(self, channel_name: str, game_name: str = None, title: str = None) -> Stream:
        db = SessionLocal()
        try:
            active_stream = self.get_active_stream(channel_name)
            if active_stream:
                logger.warning(f"Попытка начать стрим, но активный стрим уже существует: {active_stream.id}")
                return active_stream
            
            stream = Stream(channel_name=channel_name, started_at=datetime.utcnow(), game_name=game_name, title=title, is_active=True)
            
            db.add(stream)
            db.commit()
            db.refresh(stream)
            
            logger.info(f"Начат новый стрим: ID {stream.id}, канал {channel_name}, игра: {game_name}")
            return stream
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при начале стрима: {e}")
            raise
        finally:
            db.close()

    def end_stream(self, active_stream_id: int, finish_time):
        db = SessionLocal()
        try:
            stream = db.query(Stream).filter_by(id=active_stream_id).first()
            stream.ended_at = finish_time
            stream.is_active = False
            stream.updated_at = datetime.utcnow()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при завершении стрима: {e}")
            return None
        finally:
            db.close()

    def update_stream_total_viewers(self, stream_id: int, total_viewers: int):
        db = SessionLocal()
        try:
            stream = db.query(Stream).filter_by(id=stream_id).first()
            stream.total_viewers = total_viewers
            stream.updated_at = datetime.utcnow()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении total_viewers: {e}")
            return None
        finally:
            db.close()
    
    def end_stream(self, channel_name: str) -> Optional[Stream]:
        db = SessionLocal()
        try:
            stream = db.query(Stream).filter_by(channel_name=channel_name, is_active=True).first()
            
            if not stream:
                logger.warning(f"Нет активного стрима для завершения в канале {channel_name}")
                return None
            
            stream.ended_at = datetime.utcnow()
            stream.is_active = False
            stream.updated_at = datetime.utcnow()
            
            active_sessions = db.query(StreamViewerSession).filter_by(stream_id=stream.id, is_watching=True).all()
            
            for session in active_sessions:
                if session.session_start:
                    session_duration = datetime.utcnow() - session.session_start
                    session_minutes = int(session_duration.total_seconds() / 60)
                    session.total_minutes += session_minutes
                
                session.session_end = datetime.utcnow()
                session.is_watching = False
                session.updated_at = datetime.utcnow()
            
            total_unique_viewers = (
                db.query(StreamViewerSession.user_name)
                .filter_by(stream_id=stream.id)
                .distinct()
                .count()
            )
            stream.total_viewers = total_unique_viewers
            
            db.commit()
            db.refresh(stream)
            return stream
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при завершении стрима: {e}")
            return None
        finally:
            db.close()
    
    def get_active_stream(self, channel_name: str) -> Optional[Stream]:
        db = SessionLocal()
        try:
            return db.query(Stream).filter_by(channel_name=channel_name, is_active=True).first()
        except Exception as e:
            logger.error(f"Ошибка при получении активного стрима: {e}")
            return None
        finally:
            db.close()
    
    def update_stream_metadata(self, channel_name: str, game_name: str = None, title: str = None):
        db = SessionLocal()
        try:
            stream = db.query(Stream).filter_by(channel_name=channel_name, is_active=True).first()
            
            if not stream:
                return
            
            if game_name is not None:
                stream.game_name = game_name
            if title is not None:
                stream.title = title
            
            stream.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении метаданных стрима: {e}")
        finally:
            db.close()
    
    def get_stream_history(self, channel_name: str, limit: int = 10) -> List[Stream]:
        db = SessionLocal()
        try:
            streams = (
                db.query(Stream)
                .filter_by(channel_name=channel_name)
                .order_by(Stream.started_at.desc())
                .limit(limit)
                .all()
            )
            
            return streams
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории стримов: {e}")
            return []
        finally:
            db.close()

    def update_max_concurrent_viewers_count(self, active_stream_id: int, viewers_count: int):
        db = SessionLocal()
        try:
            stream = db.query(Stream).filter_by(id=active_stream_id).first()
            stream.max_concurrent_viewers = viewers_count
            stream.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении concurrent viewers: {e}")
            db.rollback()
        finally:
            db.close()