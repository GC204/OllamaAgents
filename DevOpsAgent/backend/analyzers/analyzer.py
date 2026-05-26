from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from .fast_detector import FastDetector
from .deep_detector import DeepDetector

logger = logging.getLogger(__name__)


class StackProfile(BaseModel):
    """Stack profile data model."""
    languages: list
    build_tools: list
    testing_frameworks: list
    frameworks: Dict[str, list]
    dependencies: Optional[Dict] = None
    architecture_patterns: Optional[Dict] = None
    existing_ci_cd: Optional[Dict] = None
    configuration_files: Optional[Dict] = None


class CodebaseAnalyzer:
    """Orchestrator for codebase analysis."""
    
    def __init__(self, repo_path: str):
        """
        Initialize codebase analyzer.
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path
        self.fast_detector = FastDetector(repo_path)
        self.deep_detector = DeepDetector(repo_path)
    
    def analyze(self, deep: bool = False) -> StackProfile:
        """
        Analyze codebase stack.
        
        Args:
            deep: Whether to perform deep analysis (dependency parsing, architecture detection)
                 
        Returns:
            StackProfile with detected technologies
        """
        try:
            logger.info(f"Starting codebase analysis (deep={deep}) for {self.repo_path}")
            
            # Fast detection (always performed)
            quick_scan = self.fast_detector.get_quick_scan()
            
            profile = StackProfile(
                languages=quick_scan["languages"],
                build_tools=quick_scan["build_tools"],
                testing_frameworks=quick_scan["testing_frameworks"],
                frameworks=quick_scan["frameworks"]
            )
            
            # Deep analysis (optional)
            if deep:
                logger.info("Performing deep analysis...")
                full_analysis = self.deep_detector.get_full_analysis()
                
                profile.dependencies = full_analysis["dependencies"]
                profile.architecture_patterns = full_analysis["architecture"]
                profile.existing_ci_cd = full_analysis["existing_ci_cd"]
                profile.configuration_files = full_analysis["configuration_files"]
                
                logger.info("Deep analysis completed")
            
            logger.info(f"Analysis complete: {len(profile.languages)} languages detected")
            return profile
        
        except Exception as e:
            logger.error(f"Error analyzing codebase: {e}")
            raise
    
    def get_primary_language(self, profile: StackProfile) -> Optional[str]:
        """
        Get primary programming language from profile.
        
        Args:
            profile: StackProfile object
            
        Returns:
            Primary language name or None
        """
        if not profile.languages:
            return None
        
        # Prioritize based on common patterns
        priority = ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust"]
        for lang in priority:
            if lang in profile.languages:
                return lang
        
        # Return first detected
        return profile.languages[0]
    
    def get_ci_recommendations(self, profile: StackProfile) -> Dict[str, Any]:
        """
        Get CI/CD recommendations based on detected stack.
        
        Args:
            profile: StackProfile object
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "jobs": [],
            "triggers": [],
            "cache": False,
            "artifacts": [],
        }
        
        try:
            # Build job
            if profile.build_tools:
                recommendations["jobs"].append({
                    "name": "build",
                    "tools": profile.build_tools
                })
            
            # Test job
            if profile.testing_frameworks:
                recommendations["jobs"].append({
                    "name": "test",
                    "frameworks": profile.testing_frameworks
                })
            
            # Lint job (if applicable)
            if "TypeScript" in profile.languages or "JavaScript" in profile.languages:
                recommendations["jobs"].append({
                    "name": "lint",
                    "tools": ["ESLint"]
                })
            
            # Cache recommendations
            if profile.build_tools:
                recommendations["cache"] = True
            
            # Artifact patterns
            if "Python" in profile.languages:
                recommendations["artifacts"].extend(["dist/", "build/"])
            if "JavaScript" in profile.languages or "TypeScript" in profile.languages:
                recommendations["artifacts"].extend(["dist/", "build/"])
            
            # Trigger recommendations
            recommendations["triggers"] = ["push", "pull_request"]
            
            # If containerized, add image build
            if profile.existing_ci_cd and bool(profile.architecture_patterns):
                if profile.architecture_patterns.get("containerized"):
                    recommendations["jobs"].append({
                        "name": "build-image",
                        "tools": ["Docker"]
                    })
            
            logger.info(f"Generated recommendations: {len(recommendations['jobs'])} jobs")
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def summarize(self, profile: StackProfile) -> str:
        """
        Generate a text summary of detected stack.
        
        Args:
            profile: StackProfile object
            
        Returns:
            Summary string
        """
        summary = []
        
        if profile.languages:
            summary.append(f"Languages: {', '.join(profile.languages)}")
        
        if profile.build_tools:
            summary.append(f"Build Tools: {', '.join(profile.build_tools)}")
        
        if profile.testing_frameworks:
            summary.append(f"Testing: {', '.join(profile.testing_frameworks)}")
        
        frontend_frameworks = profile.frameworks.get("frontend", [])
        if frontend_frameworks:
            summary.append(f"Frontend: {', '.join(frontend_frameworks)}")
        
        backend_frameworks = profile.frameworks.get("backend", [])
        if backend_frameworks:
            summary.append(f"Backend: {', '.join(backend_frameworks)}")
        
        if profile.architecture_patterns:
            patterns = [k for k, v in profile.architecture_patterns.items() if v]
            if patterns:
                summary.append(f"Architecture: {', '.join(patterns)}")
        
        if profile.existing_ci_cd:
            existing = [k for k, v in profile.existing_ci_cd.items() if v]
            if existing:
                summary.append(f"Existing CI/CD: {', '.join(existing)}")
        
        return "\n".join(summary) if summary else "No stack detected"
