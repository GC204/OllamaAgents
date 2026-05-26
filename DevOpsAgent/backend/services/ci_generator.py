import yaml
import logging
import re
from typing import Tuple, Optional

from llm.ollama_client import OllamaClient
from llm.prompts import (
    format_ci_generator_prompt,
    CI_GENERATOR_SYSTEM_PROMPT,
    YAML_VALIDATION_PROMPT
)
from config.settings import get_settings

logger = logging.getLogger(__name__)


class CIGenerator:
    """Service for generating GitHub Actions CI/CD workflows."""
    
    def __init__(self):
        """Initialize CI generator."""
        settings = get_settings()
        self.ollama_client = OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )
        self.max_retries = 3
    
    def generate_ci(
        self,
        repo_name: str,
        release_branch: str,
        languages: list,
        frameworks: dict,
        build_tools: list,
        testing_frameworks: list,
        stack_summary: str,
        user_requirements: str
    ) -> Tuple[str, bool]:
        """
        Generate GitHub Actions CI/CD workflow.
        
        Args:
            repo_name: Repository name
            release_branch: Target branch for CI
            languages: List of programming languages
            frameworks: Dictionary of frameworks by type
            build_tools: List of build tools
            testing_frameworks: List of testing frameworks
            stack_summary: Text summary of stack
            user_requirements: User's CI requirements
            
        Returns:
            Tuple of (YAML content, is_valid)
        """
        try:
            logger.info(f"Generating CI for {repo_name}")
            
            # Ensure Ollama is available
            if not self.ollama_client.is_available():
                logger.error("Ollama server not available")
                return self._get_fallback_ci(repo_name, release_branch), False
            
            # Format prompt
            prompt = format_ci_generator_prompt(
                repo_name=repo_name,
                release_branch=release_branch,
                languages=languages,
                frameworks=frameworks,
                build_tools=build_tools,
                testing_frameworks=testing_frameworks,
                stack_summary=stack_summary,
                user_requirements=user_requirements
            )
            
            # Generate YAML
            full_prompt = f"{CI_GENERATOR_SYSTEM_PROMPT}\n\n{prompt}"
            yaml_content = self.ollama_client.generate(
                prompt=full_prompt,
                temperature=0.3,  # Lower temp for more consistent output
                top_p=0.9,
                top_k=40
            )
            
            if not yaml_content:
                logger.error("Failed to generate YAML from Ollama")
                return self._get_fallback_ci(repo_name, release_branch), False
            
            # Clean up response (remove markdown code blocks if present)
            yaml_content = self._clean_yaml_response(yaml_content)
            
            # Validate YAML
            is_valid, errors = self._validate_yaml(yaml_content)
            
            if not is_valid:
                logger.warning(f"Generated YAML has issues: {errors}")
                # Attempt to fix and retry
                for attempt in range(self.max_retries):
                    logger.info(f"Attempting to fix YAML (attempt {attempt + 1})")
                    fixed_yaml = self._attempt_fix(yaml_content, errors)
                    is_valid_fixed, _ = self._validate_yaml(fixed_yaml)
                    if is_valid_fixed:
                        logger.info("Successfully fixed YAML")
                        return fixed_yaml, True
                
                logger.warning("Could not fix YAML, returning as-is")
            
            return yaml_content, is_valid
        
        except Exception as e:
            logger.error(f"Error generating CI: {e}")
            return self._get_fallback_ci(repo_name, release_branch), False
    
    def _validate_yaml(self, yaml_content: str) -> Tuple[bool, list]:
        """
        Validate GitHub Actions YAML.
        
        Args:
            yaml_content: YAML content to validate
            
        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []
        
        try:
            # Check for hardcoded secrets
            if self._contains_secrets(yaml_content):
                errors.append("Contains potential hardcoded secrets")
            
            # Try to parse YAML
            yaml.safe_load(yaml_content)
            
            # Check for required top-level keys
            if "name:" not in yaml_content:
                errors.append("Missing 'name' field")
            
            if "on:" not in yaml_content:
                errors.append("Missing 'on' (triggers) field")
            
            if "jobs:" not in yaml_content:
                errors.append("Missing 'jobs' field")
            
            # Check for at least one job
            if yaml_content.count("runs-on:") == 0:
                errors.append("No jobs with 'runs-on' specified")
            
            return len(errors) == 0, errors
        
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {str(e)}")
            return False, errors
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def _attempt_fix(self, yaml_content: str, errors: list) -> str:
        """
        Attempt to fix YAML based on identified errors.
        
        Args:
            yaml_content: Original YAML content
            errors: List of errors
            
        Returns:
            Fixed YAML content
        """
        fixed = yaml_content
        
        # Remove markdown code blocks
        fixed = fixed.replace("```yaml", "").replace("```yml", "").replace("```", "")
        
        # Ensure proper indentation
        fixed = self._fix_indentation(fixed)
        
        # Ensure required fields exist
        if "name:" not in fixed:
            fixed = "name: CI/CD Workflow\n" + fixed
        
        if "on:" not in fixed:
            fixed = fixed + "\non:\n  push:\n    branches: [main, develop]\n"
        
        if "jobs:" not in fixed:
            fixed = fixed + "\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
        
        return fixed
    
    def _fix_indentation(self, yaml_content: str) -> str:
        """Fix YAML indentation issues."""
        try:
            data = yaml.safe_load(yaml_content)
            return yaml.dump(data, default_flow_style=False, sort_keys=False)
        except:
            return yaml_content
    
    def _contains_secrets(self, yaml_content: str) -> bool:
        """Check if YAML contains potential hardcoded secrets."""
        secret_patterns = [
            r'password\s*[:=]\s*[\'"]([^\'\"]+)[\'"]',
            r'secret\s*[:=]\s*[\'"]([^\'\"]+)[\'"]',
            r'token\s*[:=]\s*[\'"]([^\'\"]+)[\'"]',
            r'api[_-]?key\s*[:=]\s*[\'"]([^\'\"]+)[\'"]',
            r'BEGIN\s+RSA\s+PRIVATE\s+KEY',
            r'BEGIN\s+OPENSSH\s+PRIVATE\s+KEY',
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, yaml_content, re.IGNORECASE):
                return True
        
        return False
    
    def _clean_yaml_response(self, response: str) -> str:
        """Clean up LLM response to extract pure YAML."""
        # Remove markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            # Remove opening and closing backticks
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines)
        
        return response.strip()
    
    def _get_fallback_ci(self, repo_name: str, release_branch: str) -> str:
        """Get a basic fallback CI workflow."""
        fallback = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ {release_branch} ]
  pull_request:
    branches: [ {release_branch} ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup environment
        run: |
          echo "Setting up CI for {repo_name}"
          
      - name: Check for dependencies
        run: |
          if [ -f requirements.txt ]; then echo "Python project"; fi
          if [ -f package.json ]; then echo "Node.js project"; fi
          if [ -f go.mod ]; then echo "Go project"; fi
          if [ -f pom.xml ]; then echo "Maven project"; fi
          
      - name: Build
        run: echo "Build step - update based on your project"
        
      - name: Test
        run: echo "Test step - update based on your project"
"""
        return fallback
