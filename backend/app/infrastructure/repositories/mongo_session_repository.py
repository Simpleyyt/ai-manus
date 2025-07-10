from typing import Optional, List
from datetime import datetime, UTC
import uuid
import secrets
from app.domain.models.session import Session, SessionStatus
from app.domain.models.file import FileInfo
from app.domain.repositories.session_repository import SessionRepository
from app.domain.events.agent_events import BaseEvent
from app.infrastructure.models.documents import SessionDocument
import logging

logger = logging.getLogger(__name__)

class MongoSessionRepository(SessionRepository):
    """MongoDB implementation of SessionRepository"""
    
    async def save(self, session: Session) -> None:
        """Save or update a session"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.session_id == session.id
        )
        
        if not mongo_session:
            mongo_session = self._to_mongo_session(session)
            await mongo_session.save()
            return
        
        # Update fields from session domain model
        session_data = session.model_dump(exclude={'id', 'created_at'})
        session_data['session_id'] = session.id
        session_data['updated_at'] = datetime.now(UTC)
        
        for field, value in session_data.items():
            setattr(mongo_session, field, value)
        await mongo_session.save()


    async def find_by_id(self, session_id: str) -> Optional[Session]:
        """Find a session by its ID"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        )
        return self._to_domain_session(mongo_session) if mongo_session else None
    
    async def update_title(self, session_id: str, title: str) -> None:
        """Update the title of a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$set": {"title": title, "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def update_latest_message(self, session_id: str, message: str, timestamp: datetime) -> None:
        """Update the latest message of a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$set": {"latest_message": message, "latest_message_at": timestamp, "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def add_event(self, session_id: str, event: BaseEvent) -> None:
        """Add an event to a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$push": {"events": event}, "$set": {"updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def add_file(self, session_id: str, file_info: FileInfo) -> None:
        """Add a file to a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$push": {"files": file_info}, "$set": {"updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def remove_file(self, session_id: str, file_id: str) -> None:
        """Remove a file from a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$pull": {"files": {"file_id": file_id}}, "$set": {"updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def get_file_by_path(self, session_id: str, file_path: str) -> Optional[FileInfo]:
        """Get file by path from a session"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        )
        if not mongo_session:
            raise ValueError(f"Session {session_id} not found")
        
        # Search for file with matching path
        for file_info in mongo_session.files:
            if file_info.file_path == file_path:
                return file_info
        return None

    async def delete(self, session_id: str) -> None:
        """Delete a session"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        )
        if mongo_session:
            await mongo_session.delete()

    async def get_all(self) -> List[Session]:
        """Get all sessions"""
        mongo_sessions = await SessionDocument.find().sort("-latest_message_at").to_list()
        return [self._to_domain_session(mongo_session) for mongo_session in mongo_sessions]
    
    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        """Update the status of a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$set": {"status": status, "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def update_unread_message_count(self, session_id: str, count: int) -> None:
        """Update the unread message count of a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$set": {"unread_message_count": count, "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def increment_unread_message_count(self, session_id: str) -> None:
        """Atomically increment the unread message count of a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$inc": {"unread_message_count": 1}, "$set": {"updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def decrement_unread_message_count(self, session_id: str) -> None:
        """Atomically decrement the unread message count of a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$inc": {"unread_message_count": -1}, "$set": {"updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def share_session(self, session_id: str) -> None:
        """Share a session and generate share ID"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        )
        if not mongo_session:
            raise ValueError(f"Session {session_id} not found")
        
        # 生成分享ID和访问令牌
        share_id = uuid.uuid4().hex[:16]
        share_token = secrets.token_urlsafe(32)
        
        # 更新会话
        result = await mongo_session.update(
            {"$set": {
                "share_id": share_id,
                "is_shared": True,
                "shared_at": datetime.now(UTC),
                "share_token": share_token,
                "updated_at": datetime.now(UTC)
            }}
        )
        if not result:
            raise ValueError(f"Failed to share session {session_id}")

    async def unshare_session(self, session_id: str) -> None:
        """Unshare a session"""
        result = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        ).update(
            {"$set": {
                "share_id": None,
                "is_shared": False,
                "shared_at": None,
                "share_token": None,
                "updated_at": datetime.now(UTC)
            }}
        )
        if not result:
            raise ValueError(f"Session {session_id} not found")

    async def find_by_share_id(self, share_id: str) -> Optional[Session]:
        """根据分享ID查找会话
        
        Args:
            share_id: 分享ID
            
        Returns:
            会话信息，如果不存在则返回None
        """
        doc = await SessionDocument.find_one({"share_id": share_id})
        if not doc:
            return None
        return self._to_domain_session(doc)

    async def update(self, session: Session) -> None:
        """更新会话
        
        Args:
            session: 会话信息
        """
        doc = await SessionDocument.find_one({"session_id": session.id})
        if not doc:
            return
            
        # 更新文档
        doc.share_id = session.share_id
        doc.share_token = session.share_token
        doc.is_shared = session.is_shared
        doc.shared_at = session.shared_at
        doc.updated_at = datetime.now(UTC)
        
        await doc.save()

    async def validate_share_token(self, share_id: str, token: str) -> bool:
        """Validate share token for a shared session"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.share_id == share_id
        )
        if not mongo_session or not mongo_session.share_token:
            return False
        return secrets.compare_digest(mongo_session.share_token, token)

    async def get_timeline(self, session_id: str) -> List[dict]:
        """Get timeline data for session playback"""
        mongo_session = await SessionDocument.find_one(
            SessionDocument.session_id == session_id
        )
        if not mongo_session:
            raise ValueError(f"Session {session_id} not found")

        timeline = []
        for event in mongo_session.events:
            # 根据事件类型构建时间线点
            point = {
                "timestamp": int(event.timestamp.timestamp()),
                "type": self._get_event_type(event),
                "content": self._get_event_content(event),
                "details": self._get_event_details(event)
            }
            timeline.append(point)
        
        return timeline

    def _to_domain_session(self, mongo_session: SessionDocument) -> Session:
        """Convert MongoDB document to domain model"""
        # Convert to dict and map session_id to id field
        session_data = mongo_session.model_dump(exclude={'id'})
        session_data['id'] = session_data.pop('session_id')
        return Session.model_validate(session_data)
    
    def _to_mongo_session(self, session: Session) -> SessionDocument:
        """Convert domain session to MongoDB document"""
        # Convert to dict and map id to session_id field
        session_data = session.model_dump()
        session_data['session_id'] = session_data.pop('id')
        return SessionDocument.model_validate(session_data)

    def _get_event_type(self, event: BaseEvent) -> str:
        """根据事件类型确定时间线点类型"""
        event_type = event.__class__.__name__
        if "Think" in event_type:
            return "thinking"
        elif "Tool" in event_type:
            return "action"
        elif "Plan" in event_type:
            return "decision"
        elif "Message" in event_type:
            return "info"
        else:
            return "solution"

    def _get_event_content(self, event: BaseEvent) -> str:
        """获取事件的主要内容"""
        if hasattr(event, "message"):
            return event.message
        elif hasattr(event, "content"):
            return event.content
        else:
            return str(event)

    def _get_event_details(self, event: BaseEvent) -> dict:
        """获取事件的详细信息"""
        details = event.model_dump(exclude={"timestamp"})
        if "message" in details:
            del details["message"]
        if "content" in details:
            del details["content"]
        return details
