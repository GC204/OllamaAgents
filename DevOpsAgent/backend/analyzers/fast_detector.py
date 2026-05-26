import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class FastDetector:
    """Fast codebase stack detection using file scanning."""
    
    # Language signatures
    LANGUAGE_SIGNATURES = {
        "Python": ["*.py", "*.pz", "requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
        "JavaScript": ["*.js", "*.mjs", "*.cjs", "package.json"],
        "TypeScript": ["*.ts", "*.tsx", "tsconfig.json"],
        "Java": ["*.java", "pom.xml", "build.gradle", "build.gradle.kts"],
        "Go": ["*.go", "go.mod", "go.sum"],
        "Rust": ["*.rs", "Cargo.toml", "Cargo.lock"],
        "C#": ["*.cs", "*.csproj", "*.sln"],
        "Ruby": ["*.rb", "Gemfile", "*.gemspec"],
        "PHP": ["*.php", "composer.json"],
    }
    
    # Build tools
    BUILD_TOOLS = {
        "npm": "package.json",
        "yarn": "yarn.lock",
        "pnpm": "pnpm-lock.yaml",
        "Maven": "pom.xml",
        "Gradle": ["build.gradle", "build.gradle.kts"],
        "Cargo": "Cargo.toml",
        "pip": "requirements.txt",
        "poetry": "pypoetry.lock",
        "dotnet": ".csproj",
    }
    
    # Testing frameworks
    TESTING_FRAMEWORKS = {
        "pytest": "pytest",
        "unittest": "unittest",
        "Jest": "jest",
        "Mocha": "mocha",
        "Jasmine": "jasmine",
        "JUnit": "junit",
        "TestNG": "testng",
        "xUnit": "xunit",
        "NUnit": "nunit",
        "Rust": "cargo test",
    }
    
    def __init__(self, repo_path: str):
        """
        Initialize fast detector.
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
    
    def detect_languages(self) -> List[str]:
        """
        Detect programming languages in repository.
        
        Returns:
            List of detected languages
        """
        detected = set()
        
        try:
            for language, patterns in self.LANGUAGE_SIGNATURES.items():
                if self._has_files(patterns):
                    detected.add(language)
                    logger.info(f"Detected language: {language}")
        except Exception as e:
            logger.error(f"Error detecting languages: {e}")
        
        return sorted(list(detected))
    
    def detect_build_tools(self) -> List[str]:
        """
        Detect build tools used in repository.
        
        Returns:
            List of detected build tools
        """
        detected = set()
        
        try:
            for tool, patterns in self.BUILD_TOOLS.items():
                if isinstance(patterns, str):
                    patterns = [patterns]
                if self._has_files(patterns):
                    detected.add(tool)
                    logger.info(f"Detected build tool: {tool}")
        except Exception as e:
            logger.error(f"Error detecting build tools: {e}")
        
        return sorted(list(detected))
    
    def detect_testing_frameworks(self) -> List[str]:
        """
        Detect testing frameworks by language patterns.
        
        Returns:
            List of detected testing frameworks
        """
        detected = set()
        languages = self.detect_languages()
        
        try:
            # Add language-specific defaults
            if "Python" in languages:
                detected.add("pytest")
            if "JavaScript" in languages or "TypeScript" in languages:
                detected.add("Jest")
            if "Java" in languages:
                detected.add("JUnit")
            if "Rust" in languages:
                detected.add("Cargo test")
            
            logger.info(f"Detected testing frameworks: {detected}")
        except Exception as e:
            logger.error(f"Error detecting testing frameworks: {e}")
        
        return sorted(list(detected))
    
    def detect_frameworks(self) -> Dict[str, List[str]]:
        """
        Detect popular frameworks by scanning package files.
        
        Returns:
            Dictionary of framework types and detected frameworks
        """
        frameworks = {
            "frontend": [],
            "backend": [],
            "mobile": [],
            "other": []
        }
        
        try:
            # Check package.json for frontend/backend frameworks
            package_json = self.repo_path / "package.json"
            if package_json.exists():
                frameworks.update(self._detect_npm_frameworks(package_json))
            
            # Check requirements.txt for Python frameworks
            req_txt = self.repo_path / "requirements.txt"
            if req_txt.exists():
                frameworks.update(self._detect_python_frameworks(req_txt))
            
            # Check pom.xml for Java frameworks
            pom_xml = self.repo_path / "pom.xml"
            if pom_xml.exists():
                frameworks.update(self._detect_java_frameworks(pom_xml))
            
            logger.info(f"Detected frameworks: {frameworks}")
        except Exception as e:
            logger.error(f"Error detecting frameworks: {e}")
        
        return frameworks
    
    def _has_files(self, patterns: List[str]) -> bool:
        """
        Check if any files matching patterns exist in repo.
        
        Args:
            patterns: List of glob patterns
            
        Returns:
            True if any files match
        """
        try:
            for pattern in patterns:
                # Direct file check
                if (self.repo_path / pattern).exists():
                    return True
                
                # Glob pattern check
                if list(self.repo_path.glob(f"**/{pattern}")):
                    return True
        except Exception as e:
            logger.debug(f"Error checking files for patterns {patterns}: {e}")
        
        return False
    
    def _detect_npm_frameworks(self, package_json: Path) -> Dict[str, List[str]]:
        """Detect frameworks from package.json."""
        frameworks = {"frontend": [], "backend": [], "mobile": [], "other": []}
        
        try:
            with open(package_json, "r") as f:
                data = json.load(f)
            
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            
            # Frontend frameworks
            if "react" in deps:
                frameworks["frontend"].append("React")
            if "vue" in deps:
                frameworks["frontend"].append("Vue.js")
            if "angular" in deps:
                frameworks["frontend"].append("Angular")
            if "svelte" in deps:
                frameworks["frontend"].append("Svelte")
            
            # Backend frameworks
            if "express" in deps:
                frameworks["backend"].append("Express.js")
            if "nestjs" in deps:
                frameworks["backend"].append("NestJS")
            if "fastify" in deps:
                frameworks["backend"].append("Fastify")
            if "hapi" in deps:
                frameworks["backend"].append("Hapi")
            
            # Mobile frameworks
            if "react-native" in deps:
                frameworks["mobile"].append("React Native")
            
            logger.debug(f"Detected NPM frameworks: {frameworks}")
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
        
        return frameworks
    
    def _detect_python_frameworks(self, req_txt: Path) -> Dict[str, List[str]]:
        """Detect frameworks from requirements.txt."""
        frameworks = {"frontend": [], "backend": [], "mobile": [], "other": []}
        
        try:
            with open(req_txt, "r") as f:
                content = f.read().lower()
            
            # Backend frameworks
            if "django" in content:
                frameworks["backend"].append("Django")
            if "flask" in content:
                frameworks["backend"].append("Flask")
            if "fastapi" in content:
                frameworks["backend"].append("FastAPI")
            if "sqlalchemy" in content:
                frameworks["other"].append("SQLAlchemy")
            
            # Data science
            if "pandas" in content:
                frameworks["other"].append("Pandas")
            if "numpy" in content:
                frameworks["other"].append("NumPy")
            
            logger.debug(f"Detected Python frameworks: {frameworks}")
        except Exception as e:
            logger.debug(f"Error parsing requirements.txt: {e}")
        
        return frameworks
    
    def _detect_java_frameworks(self, pom_xml: Path) -> Dict[str, List[str]]:
        """Detect frameworks from pom.xml."""
        frameworks = {"frontend": [], "backend": [], "mobile": [], "other": []}
        
        try:
            with open(pom_xml, "r") as f:
                content = f.read().lower()
            
            # Backend frameworks
            if "spring-boot" in content or "spring-web" in content:
                frameworks["backend"].append("Spring Boot")
            if "micronaut" in content:
                frameworks["backend"].append("Micronaut")
            
            logger.debug(f"Detected Java frameworks: {frameworks}")
        except Exception as e:
            logger.debug(f"Error parsing pom.xml: {e}")
        
        return frameworks
    
    def get_quick_scan(self) -> Dict:
        """
        Get quick scan results.
        
        Returns:
            Dictionary with detected technologies
        """
        return {
            "languages": self.detect_languages(),
            "build_tools": self.detect_build_tools(),
            "testing_frameworks": self.detect_testing_frameworks(),
            "frameworks": self.detect_frameworks()
        }
