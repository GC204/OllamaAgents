from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
import uuid

from config.db import Base


class CIStatus(str, enum.Enum):
    """CI generation status enumeration."""
    PENDING = "pending"
    GENERATED = "generated"
    PR_CREATED = "pr_created"
    APPROVED = "approved"
    MERGED = "merged"
    FAILED = "failed"


class GeneratedCI(Base):
    """GeneratedCI model for storing generated CI/CD configurations."""
    __tablename__ = "generated_ci"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    repo_name = Column(String(255), nullable=False)
    branch = Column(String(255), nullable=True)
    yaml_content = Column(Text, nullable=True)
    pr_url = Column(String(500), nullable=True)
    pr_number = Column(String(10), nullable=True)
    status = Column(SQLEnum(CIStatus), default=CIStatus.PENDING)
    approval_timestamp = Column(DateTime, nullable=True)
    merge_timestamp = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GeneratedCI {self.id} - {self.repo_name}>"
