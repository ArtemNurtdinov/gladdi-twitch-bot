import logging
from typing import Optional, List
from datetime import datetime
from db.database import SessionLocal
from features.stream.db.stream import Stream
from features.stream.db.stream_viewer_session import StreamViewerSession

logger = logging.getLogger(__name__)


class StreamService:

    def __init__(self):
        pass
    
    def start_stream(self, channel_name: str, game_name: str = None, title: str = None) -> Stream:
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
    
    def end_stream(self, channel_name: str) -> Optional[Stream]:
        db = SessionLocal()
        try:
            stream = (
                db.query(Stream)
                .filter_by(channel_name=channel_name, is_active=True)
                .first()
            )
            
            if not stream:
                logger.warning(f"Нет активного стрима для завершения в канале {channel_name}")
                return None
            
            stream.ended_at = datetime.utcnow()
            stream.is_active = False
            stream.updated_at = datetime.utcnow()
            
            active_sessions = (
                db.query(StreamViewerSession)
                .filter_by(stream_id=stream.id, is_watching=True)
                .all()
            )
            
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
            
            logger.info(f"Стрим завершен: ID {stream.id}, длительность: {stream.get_formatted_duration()}, зрителей: {total_unique_viewers}")
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
            stream = (
                db.query(Stream)
                .filter_by(channel_name=channel_name, is_active=True)
                .first()
            )
            
            if stream:
                db.refresh(stream)
            
            return stream
            
        except Exception as e:
            logger.error(f"Ошибка при получении активного стрима: {e}")
            return None
        finally:
            db.close()
    
    def update_stream_metadata(self, channel_name: str, game_name: str = None, title: str = None) -> bool:
        db = SessionLocal()
        try:
            stream = (
                db.query(Stream)
                .filter_by(channel_name=channel_name, is_active=True)
                .first()
            )
            
            if not stream:
                return False
            
            if game_name is not None:
                stream.game_name = game_name
            if title is not None:
                stream.title = title
            
            stream.updated_at = datetime.utcnow()
            
            db.commit()
            logger.debug(f"Обновлены метаданные стрима {stream.id}: игра={game_name}, название={title}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении метаданных стрима: {e}")
            return False
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

    def update_concurrent_viewers_count(self, channel_name: str) -> Optional[int]:
        db = SessionLocal()
        try:
            active_stream = self.get_active_stream(channel_name)
            if not active_stream:
                logger.debug(f"Нет активного стрима для обновления concurrent viewers в канале {channel_name}")
                return None
            
            current_concurrent = (
                db.query(StreamViewerSession)
                .filter_by(stream_id=active_stream.id, is_watching=True)
                .count()
            )
            
            stream = db.query(Stream).filter_by(id=active_stream.id).first()
            if not stream:
                return current_concurrent
            
            if current_concurrent > stream.max_concurrent_viewers:
                old_max = stream.max_concurrent_viewers
                stream.max_concurrent_viewers = current_concurrent
                stream.updated_at = datetime.utcnow()
                
                db.commit()
                logger.info(f"Новый рекорд одновременных зрителей в стриме {stream.id}: {current_concurrent} (было: {old_max})")
            
            return current_concurrent
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении concurrent viewers: {e}")
            return None
        finally:
            db.close()