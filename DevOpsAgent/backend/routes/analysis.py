from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging
import tempfile
import shutil

from config.db import get_db
from models.session import Session as SessionModel
from github_service.manager import GitHubManager
from config.settings import get_settings
from analyzers.analyzer import CodebaseAnalyzer, StackProfile

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
github_manager = GitHubManager(settings.github_pat_token)


# Pydantic schemas
class AnalysisRequest(BaseModel):
    deep: bool = False


class AnalysisResponse(BaseModel):
    languages: list
    build_tools: list
    testing_frameworks: list
    frameworks: dict
    dependencies: Optional[dict] = None
    architecture_patterns: Optional[dict] = None
    existing_ci_cd: Optional[dict] = None
    configuration_files: Optional[dict] = None
    summary: str
    recommendations: dict


@router.post("/{session_id}/analyze", response_model=AnalysisResponse)
async def analyze_codebase(
    session_id: str,
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze codebase stack for a session.
    
    Args:
        session_id: Session ID
        request: Analysis request (deep=True for full analysis)
        db: Database session
        
    Returns:
        Analysis results with stack profile and recommendations
    """
    try:
        # Verify session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Starting analysis for session {session_id}, deep={request.deep}")
        
        # Get repository
        repo = github_manager.get_repo(session.repo_name)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository '{session.repo_name}' not found"
            )
        
        # Clone repository
        repo_path = github_manager.clone_repo(repo, session_id)
        if not repo_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clone repository"
            )
        
        try:
            # Perform analysis
            analyzer = CodebaseAnalyzer(repo_path)
            profile: StackProfile = analyzer.analyze(deep=request.deep)
            
            # Get recommendations
            recommendations = analyzer.get_ci_recommendations(profile)
            
            # Get summary
            summary = analyzer.summarize(profile)
            
            logger.info(f"Analysis complete for session {session_id}")
            
            return AnalysisResponse(
                languages=profile.languages,
                build_tools=profile.build_tools,
                testing_frameworks=profile.testing_frameworks,
                frameworks=profile.frameworks,
                dependencies=profile.dependencies,
                architecture_patterns=profile.architecture_patterns,
                existing_ci_cd=profile.existing_ci_cd,
                configuration_files=profile.configuration_files,
                summary=summary,
                recommendations=recommendations
            )
        
        finally:
            # Cleanup temporary directory
            github_manager.cleanup_temp_dir(session_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing codebase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze codebase: {str(e)}"
        )


@router.post("/{session_id}/quick-analyze", response_model=AnalysisResponse)
async def quick_analyze_codebase(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Quick analysis of codebase (fast detection only, no deep parsing).
    
    Args:
        session_id: Session ID
        db: Database session
        
    Returns:
        Quick analysis results
    """
    return await analyze_codebase(
        session_id,
        AnalysisRequest(deep=False),
        db
    )
