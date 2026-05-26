from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from config.db import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(Base):
    """Session model for storing user sessions."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=True)
    release_branch = Column(String(255), nullable=True)
    user_input = Column(Text, nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Session {self.id} - {self.repo_name}>"
