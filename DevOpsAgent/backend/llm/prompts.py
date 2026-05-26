"""
Prompt templates for LLM-based CI generation.
"""

# System prompt for stack analysis
CODEBASE_ANALYZER_SYSTEM_PROMPT = """You are an expert DevOps engineer analyzing software projects.
Your task is to analyze the detected technology stack and suggest appropriate CI/CD approaches.
Be concise and practical in your recommendations.
Focus on what matters for CI/CD: languages, frameworks, testing approaches, deployment strategies."""

CODEBASE_ANALYZER_PROMPT = """Analyze the following codebase stack and provide recommendations for CI/CD:

**Repository**: {repo_name}
**URL**: {repo_url}
**Primary Language**: {primary_language}
**Languages**: {languages}
**Frameworks**: {frameworks}
**Build Tools**: {build_tools}
**Testing Frameworks**: {testing_frameworks}
**Architecture Patterns**: {architecture_patterns}
**Existing CI/CD**: {existing_ci_cd}

Based on this analysis, provide:
1. Whether to test with multiple configurations (e.g., matrix for multiple Python versions)
2. Key build steps needed
3. Testing strategy recommendations
4. Any special considerations (databases, services, etc.)
5. Artifact generation and storage needs

Keep response practical and concise. Focus on what's needed for automated testing and building."""


# System prompt for CI/CD generation
CI_GENERATOR_SYSTEM_PROMPT = """You are an expert GitHub Actions workflow engineer.
Your task is to generate production-ready GitHub Actions CI/CD workflows.
Generate only valid YAML that can run on GitHub Actions.
Follow best practices for security, performance, and maintainability.
Include necessary error handling and logging.
Output ONLY the CI/CD YAML, no explanations or markdown code blocks."""

CI_GENERATOR_PROMPT = """Generate a GitHub Actions CI/CD workflow for the following project:

**Repository**: {repo_name}
**Release Branch**: {release_branch}
**Languages**: {languages}
**Frameworks**: {frameworks}
**Build Tools**: {build_tools}
**Testing Frameworks**: {testing_frameworks}
**Stack Analysis**: {stack_summary}

**User Requirements**:
{user_requirements}

Generate a `.github/workflows/ci.yml` file that:
1. Triggers on push and pull requests to {release_branch}
2. Includes build, test, and lint jobs as appropriate
3. Uses caching where beneficial
4. Includes matrix testing if needed (e.g., multiple Python versions)
5. Has clear job names and proper error handling
6. Follows GitHub Actions best practices

For Python projects, use python-x.x / setup
For Node.js projects, use node-x.x / npm ci
For Java projects, use Maven or Gradle
For Go projects, use go version

Output MUST be valid YAML that can be directly saved to `.github/workflows/ci.yml`.
Do not include markdown code blocks or explanations. Output only the raw YAML."""


# Prompt for multi-turn chat to gather requirements
REQUIREMENTS_GATHERING_PROMPT = """You are a DevOps assistant helping users define CI/CD requirements.
Ask relevant questions based on their stack and help them clarify what they want the CI pipeline to do.
Be conversational but focused.

Stack Summary:
{stack_summary}

Previous user message: {user_input}

Based on the stack and user input, provide:
1. A friendly acknowledgment of their input
2. 1-2 clarifying questions about their CI/CD needs (deployment targets, testing requirements, artifact needs)
3. A suggestion for what you'll include in the generated workflow

Keep it friendly, concise, and directly focused on what the CI pipeline should do."""


# Validation prompt
YAML_VALIDATION_PROMPT = """Review the following GitHub Actions YAML for issues:

{yaml_content}

Check for:
1. Valid YAML syntax
2. No hardcoded credentials or secrets
3. Proper use of GitHub Actions syntax
4. Reasonable job timeouts
5. Appropriate use of caching and artifacts

If there are issues, list them. If valid, respond with "YAML is valid and ready."
Be concise."""


def get_stack_summary(profile, analyzer) -> str:
    """Generate a summary of the stack profile for prompts."""
    return analyzer.summarize(profile)


def format_requirements_gathering_prompt(stack_summary: str, user_input: str) -> str:
    """Format the requirements gathering prompt."""
    return REQUIREMENTS_GATHERING_PROMPT.format(
        stack_summary=stack_summary,
        user_input=user_input
    )


def format_ci_generator_prompt(
    repo_name: str,
    release_branch: str,
    languages: list,
    frameworks: dict,
    build_tools: list,
    testing_frameworks: list,
    stack_summary: str,
    user_requirements: str
) -> str:
    """Format the CI generator prompt."""
    frameworks_str = ", ".join([
        f + "s" for frameworks_list in frameworks.values()
        for f in frameworks_list
    ])
    
    return CI_GENERATOR_PROMPT.format(
        repo_name=repo_name,
        release_branch=release_branch,
        languages=", ".join(languages) if languages else "Unknown",
        frameworks=frameworks_str if frameworks_str else "None detected",
        build_tools=", ".join(build_tools) if build_tools else "None detected",
        testing_frameworks=", ".join(testing_frameworks) if testing_frameworks else "None detected",
        stack_summary=stack_summary,
        user_requirements=user_requirements
    )


def format_codebase_analyzer_prompt(
    repo_name: str,
    repo_url: str,
    primary_language: str,
    languages: list,
    frameworks: dict,
    build_tools: list,
    testing_frameworks: list,
    architecture_patterns: dict,
    existing_ci_cd: dict
) -> str:
    """Format the codebase analyzer prompt."""
    frameworks_str = ", ".join([
        f for frameworks_list in frameworks.values()
        for f in frameworks_list
    ])
    
    patterns_str = ", ".join([
        k for k, v in (architecture_patterns or {}).items() if v
    ])
    
    ci_cd_str = ", ".join([
        k for k, v in (existing_ci_cd or {}).items() if v
    ])
    
    return CODEBASE_ANALYZER_PROMPT.format(
        repo_name=repo_name,
        repo_url=repo_url,
        primary_language=primary_language or "Unknown",
        languages=", ".join(languages) if languages else "None detected",
        frameworks=frameworks_str if frameworks_str else "None detected",
        build_tools=", ".join(build_tools) if build_tools else "None detected",
        testing_frameworks=", ".join(testing_frameworks) if testing_frameworks else "None detected",
        architecture_patterns=patterns_str if patterns_str else "Monolithic",
        existing_ci_cd=ci_cd_str if ci_cd_str else "None detected"
    )


def format_yaml_validation_prompt(yaml_content: str) -> str:
    """Format the YAML validation prompt."""
    return YAML_VALIDATION_PROMPT.format(yaml_content=yaml_content)
