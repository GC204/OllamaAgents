import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set
import json
import logging

logger = logging.getLogger(__name__)


class DeepDetector:
    """Deep codebase analysis with dependency parsing and architecture detection."""
    
    def __init__(self, repo_path: str):
        """
        Initialize deep detector.
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
    
    def analyze_dependencies(self) -> Dict[str, List[Dict]]:
        """
        Parse and extract dependencies from all package files.
        
        Returns:
            Dictionary with dependency information by language
        """
        dependencies = {}
        
        try:
            # Python dependencies
            deps = self._parse_python_dependencies()
            if deps:
                dependencies["python"] = deps
            
            # JavaScript/TypeScript dependencies
            deps = self._parse_npm_dependencies()
            if deps:
                dependencies["javascript"] = deps
            
            # Java dependencies
            deps = self._parse_maven_dependencies()
            if deps:
                dependencies["java"] = deps
            
            # Go dependencies
            deps = self._parse_go_dependencies()
            if deps:
                dependencies["go"] = deps
            
            logger.info(f"Analyzed dependencies: {list(dependencies.keys())}")
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
        
        return dependencies
    
    def detect_architecture_patterns(self) -> Dict[str, bool]:
        """
        Detect architecture patterns in repository.
        
        Returns:
            Dictionary of detected patterns (monorepo, microservices, etc.)
        """
        patterns = {
            "monorepo": False,
            "microservices": False,
            "serverless": False,
            "containerized": False,
            "kubernetes": False,
            "infrastructure_as_code": False,
        }
        
        try:
            # Monorepo detection
            if (self.repo_path / "lerna.json").exists() or \
               (self.repo_path / "pnpm-workspace.yaml").exists() or \
               (self.repo_path / "yarn.lock").exists() and \
               len(list((self.repo_path / "**/package.json").glob("**/package.json"))) > 1:
                patterns["monorepo"] = True
            
            # Microservices detection
            if self._count_service_directories() > 2:
                patterns["microservices"] = True
            
            # Serverless detection
            if (self.repo_path / "serverless.yml").exists() or \
               (self.repo_path / "serverless.yaml").exists():
                patterns["serverless"] = True
            
            # Containerization detection
            if (self.repo_path / "Dockerfile").exists() or \
               (self.repo_path / "docker-compose.yml").exists():
                patterns["containerized"] = True
            
            # Kubernetes detection
            if (self.repo_path / "k8s").exists() or \
               list(self.repo_path.glob("**/deployment.yaml")) or \
               list(self.repo_path.glob("**/deployment.yml")):
                patterns["kubernetes"] = True
            
            # Infrastructure as Code detection
            if (self.repo_path / "terraform").exists() or \
               (self.repo_path / "bicep").exists() or \
               list(self.repo_path.glob("**/*.tf")) or \
               list(self.repo_path.glob("**/*.bicep")):
                patterns["infrastructure_as_code"] = True
            
            logger.info(f"Detected patterns: {[k for k, v in patterns.items() if v]}")
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def detect_existing_ci_cd(self) -> Dict[str, bool]:
        """
        Detect existing CI/CD configurations.
        
        Returns:
            Dictionary of detected CI/CD platforms
        """
        ci_cd = {
            "github_actions": False,
            "gitlab_ci": False,
            "jenkins": False,
            "circleci": False,
            "travis_ci": False,
            "azure_pipelines": False,
        }
        
        try:
            # GitHub Actions
            if (self.repo_path / ".github" / "workflows").exists():
                ci_cd["github_actions"] = True
            
            # GitLab CI
            if (self.repo_path / ".gitlab-ci.yml").exists():
                ci_cd["gitlab_ci"] = True
            
            # Jenkins
            if (self.repo_path / "Jenkinsfile").exists():
                ci_cd["jenkins"] = True
            
            # CircleCI
            if (self.repo_path / ".circleci" / "config.yml").exists():
                ci_cd["circleci"] = True
            
            # Travis CI
            if (self.repo_path / ".travis.yml").exists():
                ci_cd["travis_ci"] = True
            
            # Azure Pipelines
            if (self.repo_path / "azure-pipelines.yml").exists():
                ci_cd["azure_pipelines"] = True
            
            logger.info(f"Detected CI/CD: {[k for k, v in ci_cd.items() if v]}")
        except Exception as e:
            logger.error(f"Error detecting CI/CD: {e}")
        
        return ci_cd
    
    def scan_configuration_files(self) -> Dict[str, List[str]]:
        """
        Scan for important configuration files.
        
        Returns:
            Dictionary of configuration file paths by type
        """
        configs = {
            "docker": [],
            "kubernetes": [],
            "terraform": [],
            "config": [],
        }
        
        try:
            # Docker files
            configs["docker"].extend(self._find_files(["Dockerfile", "docker-compose.yml"]))
            
            # Kubernetes
            configs["kubernetes"].extend(self._find_files(["**/*.yaml", "**/*.yml"], "k8s"))
            
            # Terraform
            configs["terraform"].extend(self._find_files(["**/*.tf"], "terraform"))
            
            # Config files
            configs["config"].extend(self._find_files([
                ".env*",
                "*.conf",
                "*.config",
                ".editorconfig"
            ]))
            
            logger.info(f"Found configuration files: {sum(len(v) for v in configs.values())}")
        except Exception as e:
            logger.error(f"Error scanning configuration files: {e}")
        
        return configs
    
    def _parse_python_dependencies(self) -> List[Dict]:
        """Parse Python dependencies from requirements files."""
        dependencies = []
        
        req_files = [
            self.repo_path / "requirements.txt",
            self.repo_path / "setup.py",
            self.repo_path / "pyproject.toml",
        ]
        
        for req_file in req_files:
            if not req_file.exists():
                continue
            
            try:
                with open(req_file, "r") as f:
                    content = f.read()
                
                # Simple regex pattern to extract package names and versions
                pattern = r'([a-zA-Z0-9\-._]+)\s*(?:==|>=|<=|~=|!=|>|<)?([a-zA-Z0-9\-._]*)'
                matches = re.findall(pattern, content)
                
                for match in matches[:20]:  # Top 20
                    pkg_name, version = match
                    if pkg_name and len(pkg_name) > 2:
                        dependencies.append({
                            "name": pkg_name.lower(),
                            "version": version or "latest",
                            "source": req_file.name
                        })
                
                logger.debug(f"Parsed {len(dependencies)} Python dependencies")
            except Exception as e:
                logger.debug(f"Error parsing {req_file}: {e}")
        
        return dependencies[:20]  # Return top 20
    
    def _parse_npm_dependencies(self) -> List[Dict]:
        """Parse NPM dependencies from package.json."""
        dependencies = []
        package_json = self.repo_path / "package.json"
        
        if not package_json.exists():
            return dependencies
        
        try:
            with open(package_json, "r") as f:
                data = json.load(f)
            
            # Combine dependencies and devDependencies
            all_deps = {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {})
            }
            
            for pkg_name, version in list(all_deps.items())[:20]:
                dependencies.append({
                    "name": pkg_name,
                    "version": version,
                    "source": "package.json"
                })
            
            logger.debug(f"Parsed {len(dependencies)} NPM dependencies")
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
        
        return dependencies
    
    def _parse_maven_dependencies(self) -> List[Dict]:
        """Parse Maven dependencies from pom.xml."""
        dependencies = []
        pom_xml = self.repo_path / "pom.xml"
        
        if not pom_xml.exists():
            return dependencies
        
        try:
            tree = ET.parse(pom_xml)
            root = tree.getroot()
            
            # Define namespace
            ns = {"pom": "http://maven.apache.org/POM/4.0.0"}
            
            # Extract dependencies
            deps = root.findall(".//pom:dependency", ns)
            for dep in deps[:20]:
                artifact = dep.find("pom:artifactId", ns)
                version = dep.find("pom:version", ns)
                
                if artifact is not None:
                    dependencies.append({
                        "name": artifact.text or "unknown",
                        "version": version.text if version is not None else "latest",
                        "source": "pom.xml"
                    })
            
            logger.debug(f"Parsed {len(dependencies)} Maven dependencies")
        except Exception as e:
            logger.debug(f"Error parsing pom.xml: {e}")
        
        return dependencies
    
    def _parse_go_dependencies(self) -> List[Dict]:
        """Parse Go dependencies from go.mod."""
        dependencies = []
        go_mod = self.repo_path / "go.mod"
        
        if not go_mod.exists():
            return dependencies
        
        try:
            with open(go_mod, "r") as f:
                lines = f.readlines()
            
            in_require = False
            for line in lines:
                line = line.strip()
                
                if line.startswith("require"):
                    in_require = True
                    continue
                
                if in_require and line.startswith("("):
                    continue
                
                if in_require and line == ")":
                    in_require = False
                    continue
                
                if in_require and line:
                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies.append({
                            "name": parts[0],
                            "version": parts[1],
                            "source": "go.mod"
                        })
                        if len(dependencies) >= 20:
                            break
            
            logger.debug(f"Parsed {len(dependencies)} Go dependencies")
        except Exception as e:
            logger.debug(f"Error parsing go.mod: {e}")
        
        return dependencies
    
    def _count_service_directories(self) -> int:
        """Count potential service directories (microservices pattern)."""
        count = 0
        service_patterns = ["services", "apps", "api", "service", "src"]
        
        for pattern in service_patterns:
            pattern_dir = self.repo_path / pattern
            if pattern_dir.exists() and pattern_dir.is_dir():
                # Count subdirectories that look like services
                count += len([
                    d for d in pattern_dir.iterdir()
                    if d.is_dir() and not d.name.startswith(".")
                ])
        
        return count
    
    def _find_files(self, patterns: List[str], root_dir: str = None) -> List[str]:
        """Find files matching patterns."""
        found = []
        search_root = self.repo_path / root_dir if root_dir else self.repo_path
        
        for pattern in patterns:
            try:
                matches = list(search_root.glob(pattern))
                found.extend([str(m.relative_to(self.repo_path)) for m in matches])
            except Exception as e:
                logger.debug(f"Error finding files with pattern {pattern}: {e}")
        
        return found[:20]  # Limit to 20 files
    
    def get_full_analysis(self) -> Dict:
        """
        Get complete deep analysis results.
        
        Returns:
            Dictionary with all analysis results
        """
        return {
            "dependencies": self.analyze_dependencies(),
            "architecture": self.detect_architecture_patterns(),
            "existing_ci_cd": self.detect_existing_ci_cd(),
            "configuration_files": self.scan_configuration_files(),
        }
