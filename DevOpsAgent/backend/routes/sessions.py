from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from config.db import get_db
from models.session import Session as SessionModel, SessionStatus
from models.chat import ChatMessage as ChatMessageModel
from github_service.manager import GitHubManager
from config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
github_manager = GitHubManager(settings.github_pat_token)


# Pydantic schemas
class CreateSessionRequest(BaseModel):
    repo_name: str
    release_branch: str
    user_input: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    repo_name: str
    release_branch: Optional[str]
    user_input: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    content: str
    role: str = "user"


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new session.
    
    Args:
        request: Session creation request
        db: Database session
        
    Returns:
        Created session object
    """
    try:
        logger.info(f"Creating session for repo: {request.repo_name}")
        
        # Verify GitHub repo exists
        try:
            repo = github_manager.get_repo(request.repo_name)
            if not repo:
                logger.warning(f"Repository '{request.repo_name}' not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Repository '{request.repo_name}' not found or access denied"
                )
            logger.info(f"Repository verified: {repo.full_name}")
        except Exception as e:
            logger.error(f"GitHub error: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GitHub error: {str(e)}"
            )
        
        # Create new session
        session = SessionModel(
            repo_name=request.repo_name,
            release_branch=request.release_branch,
            user_input=request.user_input,
            status=SessionStatus.ACTIVE
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created session {session.id} for repo {request.repo_name}")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get session by ID.
    
    Args:
        session_id: Session ID
        db: Database session
        
    Returns:
        Session object
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.get("")
async def list_sessions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all sessions with pagination.
    
    Args:
        skip: Number of sessions to skip
        limit: Maximum number of sessions to return
        db: Database session
        
    Returns:
        List of sessions
    """
    sessions = db.query(SessionModel).offset(skip).limit(limit).all()
    return sessions


@router.post("/{session_id}/chat", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_chat_message(
    session_id: str,
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Add a chat message to a session.
    
    Args:
        session_id: Session ID
        request: Chat message request
        db: Database session
        
    Returns:
        Created chat message
    """
    try:
        # Verify session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Create chat message
        message = ChatMessageModel(
            session_id=session_id,
            role=request.role,
            content=request.content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.info(f"Added {request.role} message to session {session_id}")
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add chat message"
        )


@router.get("/{session_id}/chat", response_model=List[ChatMessageResponse])
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a session.
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to return
        db: Database session
        
    Returns:
        List of chat messages
    """
    # Verify session exists
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    messages = db.query(ChatMessageModel)\
        .filter(ChatMessageModel.session_id == session_id)\
        .order_by(ChatMessageModel.created_at.desc())\
        .limit(limit)\
        .all()
    
    return messages[::-1]  # Reverse to get chronological order


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a session (soft delete - just mark as completed).
    
    Args:
        session_id: Session ID
        db: Database session
    """
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Cleanup temporary directories
        github_manager.cleanup_temp_dir(session_id)
        
        # Mark as completed instead of hard delete
        session.status = SessionStatus.COMPLETED
        db.commit()
        
        logger.info(f"Deleted session {session_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
