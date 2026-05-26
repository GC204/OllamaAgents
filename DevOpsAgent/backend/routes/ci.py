from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging

from config.db import get_db
from models.session import Session as SessionModel
from models.ci import GeneratedCI, CIStatus
from models.chat import ChatMessage, MessageRole
from github_service.manager import GitHubManager
from services.pr_service import PRCreator
from config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
github_manager = GitHubManager(settings.github_pat_token)
pr_creator = PRCreator(github_manager)


# Pydantic schemas
class CreatePRRequest(BaseModel):
    ci_id: str


class ApprovePRRequest(BaseModel):
    merge_method: str = "squash"


class PRResponse(BaseModel):
    number: int
    url: str
    html_url: str
    branch: str


class PRStatusResponse(BaseModel):
    number: int
    state: str
    url: str
    merged: bool
    mergeable: bool


@router.post("/{session_id}/ci/{ci_id}/create-pr", response_model=PRResponse)
async def create_ci_pr(
    session_id: str,
    ci_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a pull request with the generated CI/CD workflow.
    
    Args:
        session_id: Session ID
        ci_id: GeneratedCI ID
        db: Database session
        
    Returns:
        PR details
    """
    try:
        # Verify session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get generated CI
        gen_ci = db.query(GeneratedCI).filter(GeneratedCI.id == ci_id).first()
        if not gen_ci:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated CI not found"
            )
        
        if not gen_ci.yaml_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No YAML content to create PR"
            )
        
        logger.info(f"Creating PR for CI {ci_id} in session {session_id}")
        
        # Create PR
        pr_info = pr_creator.create_ci_pr(
            repo_name=session.repo_name,
            yaml_content=gen_ci.yaml_content,
            release_branch=session.release_branch or "main",
            session_id=session_id
        )
        
        if not pr_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create pull request"
            )
        
        # Update GeneratedCI record
        gen_ci.pr_number = str(pr_info["number"])
        gen_ci.pr_url = pr_info["html_url"]
        gen_ci.status = CIStatus.PR_CREATED
        db.commit()
        
        # Add system message
        sys_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.SYSTEM,
            content=f"Created PR #{pr_info['number']}: {pr_info['html_url']}"
        )
        db.add(sys_msg)
        db.commit()
        
        logger.info(f"Created PR #{pr_info['number']}")
        
        return PRResponse(**pr_info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create PR: {str(e)}"
        )


@router.get("/{session_id}/ci/{ci_id}/pr-status")
async def get_pr_status(
    session_id: str,
    ci_id: str,
    db: Session = Depends(get_db)
):
    """
    Get status of generated CI PR.
    
    Args:
        session_id: Session ID
        ci_id: GeneratedCI ID
        db: Database session
        
    Returns:
        PR status information
    """
    try:
        # Verify session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get generated CI
        gen_ci = db.query(GeneratedCI).filter(GeneratedCI.id == ci_id).first()
        if not gen_ci:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated CI not found"
            )
        
        if not gen_ci.pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PR has been created yet"
            )
        
        logger.info(f"Getting PR status for {gen_ci.pr_number}")
        
        # Get PR details
        pr_details = pr_creator.get_pr_details(
            repo_name=session.repo_name,
            pr_number=int(gen_ci.pr_number)
        )
        
        if not pr_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PR not found"
            )
        
        return pr_details
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PR status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PR status: {str(e)}"
        )


@router.get("/{session_id}/ci/{ci_id}/pr-diff")
async def get_pr_diff(
    session_id: str,
    ci_id: str,
    db: Session = Depends(get_db)
):
    """
    Get diff preview of PR changes.
    
    Args:
        session_id: Session ID
        ci_id: GeneratedCI ID
        db: Database session
        
    Returns:
        Diff preview
    """
    try:
        # Verify session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get generated CI
        gen_ci = db.query(GeneratedCI).filter(GeneratedCI.id == ci_id).first()
        if not gen_ci:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated CI not found"
            )
        
        if not gen_ci.pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PR has been created yet"
            )
        
        # Get diff
        diff = pr_creator.get_diff_preview(
            repo_name=session.repo_name,
            pr_number=int(gen_ci.pr_number)
        )
        
        return {"diff": diff}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PR diff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PR diff: {str(e)}"
        )


@router.post("/{session_id}/ci/{ci_id}/approve-github")
async def approve_pr_github(
    session_id: str,
    ci_id: str,
    request: ApprovePRRequest,
    db: Session = Depends(get_db)
):
    """
    Approve and merge PR (GitHub-direct approval workflow).
    
    Args:
        session_id: Session ID
        ci_id: GeneratedCI ID
        request: Approval request with merge method
        db: Database session
        
    Returns:
        Merge result
    """
    try:
        # Verify session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get generated CI
        gen_ci = db.query(GeneratedCI).filter(GeneratedCI.id == ci_id).first()
        if not gen_ci:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated CI not found"
            )
        
        if not gen_ci.pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PR has been created yet"
            )
        
        logger.info(f"Approving PR #{gen_ci.pr_number}")
        
        # Merge PR
        if pr_creator.approve_pr(
            repo_name=session.repo_name,
            pr_number=int(gen_ci.pr_number),
            merge_method=request.merge_method
        ):
            # Update status
            gen_ci.status = CIStatus.MERGED
            db.commit()
            
            # Add system message
            sys_msg = ChatMessage(
                session_id=session_id,
                role=MessageRole.SYSTEM,
                content=f"PR #{gen_ci.pr_number} has been successfully merged!"
            )
            db.add(sys_msg)
            db.commit()
            
            logger.info(f"Successfully merged PR #{gen_ci.pr_number}")
            
            return {
                "status": "merged",
                "pr_number": int(gen_ci.pr_number),
                "message": "PR has been successfully merged"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to merge PR"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving PR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve PR: {str(e)}"
        )


@router.post("/{session_id}/ci/{ci_id}/approve-chat")
async def approve_pr_chat(
    session_id: str,
    ci_id: str,
    request: ApprovePRRequest,
    db: Session = Depends(get_db)
):
    """
    Approve PR via chat interface (chat-based approval workflow).
    
    Shows diff to user in chat and waits for confirmation.
    
    Args:
        session_id: Session ID
        ci_id: GeneratedCI ID
        request: Approval request
        db: Database session
        
    Returns:
        Approval status and next step
    """
    try:
        # Verify session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get generated CI
        gen_ci = db.query(GeneratedCI).filter(GeneratedCI.id == ci_id).first()
        if not gen_ci:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated CI not found"
            )
        
        if not gen_ci.pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PR has been created yet"
            )
        
        logger.info(f"Approval requested for PR #{gen_ci.pr_number} via chat")
        
        # Get diff for preview
        diff = pr_creator.get_diff_preview(
            repo_name=session.repo_name,
            pr_number=int(gen_ci.pr_number)
        )
        
        # Create approval message
        approval_msg = f"""## PR Approval Required

**PR Number**: #{gen_ci.pr_number}
**URL**: {gen_ci.pr_url}

### Changes:
```
{diff}
```

Please review the changes above. Reply with "approve" or "reject" to proceed."""
        
        # Store in chat
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.SYSTEM,
            content=approval_msg
        )
        db.add(user_msg)
        db.commit()
        
        return {
            "status": "awaiting_approval",
            "pr_number": int(gen_ci.pr_number),
            "diff_preview": diff,
            "message": "Please review the diff and confirm approval in chat"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat approval flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate chat approval: {str(e)}"
        )
