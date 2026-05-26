from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging

from config.db import get_db
from models.session import Session as SessionModel
from models.chat import ChatMessage, MessageRole
from models.ci import GeneratedCI, CIStatus
from llm.ollama_client import OllamaClient
from llm.prompts import (
    format_requirements_gathering_prompt,
    REQUIREMENTS_GATHERING_PROMPT,
    CI_GENERATOR_SYSTEM_PROMPT
)
from services.ci_generator import CIGenerator
from config.settings import get_settings
from analyzers.analyzer import CodebaseAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
ollama_client = OllamaClient(
    settings.ollama_base_url,
    settings.ollama_model,
    generate_timeout=settings.ollama_generate_timeout,
    pull_timeout=settings.ollama_pull_timeout,
    check_timeout=settings.ollama_check_timeout,
    max_retries=settings.ollama_max_retries
)
ci_generator = CIGenerator()


# Pydantic schemas
class ChatMessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    
    class Config:
        from_attributes = True


class GenerateCIRequest(BaseModel):
    requirements: str


@router.post("/{session_id}/ai-response")
async def get_ai_response(
    session_id: str,
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI response for user message (multi-turn conversation).
    
    Args:
        session_id: Session ID
        request: User message
        db: Database session
        
    Returns:
        AI response text
    """
    try:
        # Verify session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Store user message
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=request.content
        )
        db.add(user_msg)
        db.commit()
        
        logger.info(f"Received message in session {session_id}")
        
        # Check if Ollama is available
        if not ollama_client.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service is not available"
            )
        
        # Get conversation context
        prev_messages = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.created_at)\
            .all()
        
        # Build context for LLM
        context = f"\n".join([
            f"{msg.role}: {msg.content}" for msg in prev_messages
        ])
        
        # Get stack profile for context
        stack_summary = _get_session_stack_summary(session_id, db)
        
        # Format prompt with context
        prompt = f"""{REQUIREMENTS_GATHERING_PROMPT}

Conversation context:
{context}

Respond helpfully to guide the user in defining their CI requirements.""".format(
            stack_summary=stack_summary,
            user_input=request.content
        )
        
        # Generate AI response
        ai_response = ollama_client.generate(
            prompt=prompt,
            temperature=0.7,
            top_p=0.95,
            top_k=40
        )
        
        if not ai_response:
            # Check if the issue is likely a timeout
            logger.error(
                f"AI response generation failed for session {session_id}. "
                f"(Timeout: {settings.ollama_generate_timeout}s, Max retries: {settings.ollama_max_retries})"
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=(
                    f"LLM request timed out. Please try again. "
                    f"(Timeout limit: {settings.ollama_generate_timeout}s)"
                )
            )
        
        # Store AI response
        ai_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        db.add(ai_msg)
        db.commit()
        
        logger.info(f"Generated AI response for session {session_id}")
        
        return {
            "role": "assistant",
            "content": ai_response
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI response: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI response: {str(e)}"
        )


@router.post("/{session_id}/generate-ci")
async def generate_ci_workflow(
    session_id: str,
    request: GenerateCIRequest,
    db: Session = Depends(get_db)
):
    """
    Generate GitHub Actions CI/CD workflow based on requirements.
    
    Args:
        session_id: Session ID
        request: CI generation request with user requirements
        db: Database session
        
    Returns:
        Generated CI workflow YAML
    """
    try:
        # Verify session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Generating CI for session {session_id}")
        
        # Store user requirements in chat
        req_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=f"Generate CI with requirements: {request.requirements}"
        )
        db.add(req_msg)
        db.commit()
        
        # Get stack profile (perform quick analysis if not cached)
        stack_profile = _get_or_analyze_stack(session, session_id, db)
        
        if not stack_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze codebase"
            )
        
        # Generate CI workflow
        yaml_content, is_valid = ci_generator.generate_ci(
            repo_name=session.repo_name,
            release_branch=session.release_branch or "main",
            languages=stack_profile.get("languages", []),
            frameworks=stack_profile.get("frameworks", {}),
            build_tools=stack_profile.get("build_tools", []),
            testing_frameworks=stack_profile.get("testing_frameworks", []),
            stack_summary=_profile_to_summary(stack_profile),
            user_requirements=request.requirements
        )
        
        logger.info(f"Generated CI workflow (valid={is_valid})")
        
        # Store in database
        generated_ci = GeneratedCI(
            session_id=session_id,
            repo_name=session.repo_name,
            branch=session.release_branch or "main",
            yaml_content=yaml_content,
            status=CIStatus.GENERATED if is_valid else CIStatus.PENDING
        )
        db.add(generated_ci)
        db.commit()
        db.refresh(generated_ci)
        
        # Store AI response
        ai_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=f"Generated CI workflow. Status: {'Valid' if is_valid else 'Generated but needs review'}."
        )
        db.add(ai_msg)
        db.commit()
        
        return {
            "ci_id": generated_ci.id,
            "yaml_content": yaml_content,
            "is_valid": is_valid,
            "status": "ready_for_review"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CI: {str(e)}"
        )


def _get_session_stack_summary(session_id: str, db: Session) -> str:
    """Get cached stack summary or return empty string."""
    # This will be implemented when Phase 2 analysis caching is added
    return "Technology stack analysis in progress"

def _get_or_analyze_stack(session, session_id: str, db: Session) -> dict:
    """Get stack profile for session."""
    try:
        from github_service.manager import GitHubManager
        from analyzers.analyzer import CodebaseAnalyzer
        
        github_manager = GitHubManager(settings.github_pat_token)
        
        repo = github_manager.get_repo(session.repo_name)
        if not repo:
            return None
        
        repo_path = github_manager.clone_repo(repo, session_id)
        if not repo_path:
            return None
        
        try:
            analyzer = CodebaseAnalyzer(repo_path)
            profile = analyzer.analyze(deep=False)
            
            return {
                "languages": profile.languages,
                "frameworks": profile.frameworks,
                "build_tools": profile.build_tools,
                "testing_frameworks": profile.testing_frameworks,
                "architecture_patterns": profile.architecture_patterns,
                "existing_ci_cd": profile.existing_ci_cd
            }
        finally:
            github_manager.cleanup_temp_dir(session_id)
    
    except Exception as e:
        logger.error(f"Error analyzing stack: {e}")
        return None


def _profile_to_summary(profile: dict) -> str:
    """Convert profile dict to summary string."""
    parts = []
    
    if profile.get("languages"):
        parts.append(f"Languages: {', '.join(profile['languages'])}")
    
    if profile.get("frameworks"):
        frameworks = []
        for fw_list in profile["frameworks"].values():
            frameworks.extend(fw_list)
        if frameworks:
            parts.append(f"Frameworks: {', '.join(frameworks)}")
    
    if profile.get("build_tools"):
        parts.append(f"Build Tools: {', '.join(profile['build_tools'])}")
    
    return "\n".join(parts)
