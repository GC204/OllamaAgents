import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
import git
import logging

logger = logging.getLogger(__name__)


class GitHubManager:
    """Manager class for GitHub API interactions."""
    
    def __init__(self, pat_token: str):
        """
        Initialize GitHub manager with PAT token.
        
        Args:
            pat_token: GitHub Personal Access Token
        """
        self.pat_token = pat_token
        self.github = Github(pat_token)
        self.temp_dirs = {}
    
    def authenticate(self) -> bool:
        """
        Test GitHub authentication.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            user = self.github.get_user()
            logger.info(f"Authenticated as: {user.login}")
            return True
        except GithubException as e:
            logger.error(f"GitHub authentication failed: {e}")
            return False
    
    def get_repo(self, repo_full_name: str) -> Optional[Repository]:
        """
        Get repository object from full name (owner/repo).
        
        Args:
            repo_full_name: Repository full name (e.g., "owner/repo-name")
            
        Returns:
            Repository object or None if not found
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            logger.info(f"Found repository: {repo_full_name}")
            return repo
        except GithubException as e:
            logger.error(f"Failed to get repository {repo_full_name}: {e}")
            return None
    
    def get_repo_info(self, repo: Repository) -> Dict[str, Any]:
        """
        Get repository information.
        
        Args:
            repo: Repository object
            
        Returns:
            Dictionary with repo information
        """
        try:
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "private": repo.private,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "topics": repo.topics,
            }
        except Exception as e:
            logger.error(f"Failed to get repo info: {e}")
            return {}
    
    def clone_repo(self, repo: Repository, session_id: str) -> Optional[str]:
        """
        Clone repository to temporary directory.
        
        Args:
            repo: Repository object
            session_id: Session ID for tracking temp directories
            
        Returns:
            Path to cloned repository or None if failed
        """
        try:
            # Create temp directory with session ID
            temp_dir = tempfile.mkdtemp(prefix=f"devops_agent_{session_id}_")
            self.temp_dirs[session_id] = temp_dir
            
            logger.info(f"Cloning {repo.full_name} to {temp_dir}")
            git.Repo.clone_from(repo.clone_url, temp_dir)
            
            logger.info(f"Successfully cloned repository to {temp_dir}")
            return temp_dir
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            if session_id in self.temp_dirs:
                self._cleanup_temp_dir(session_id)
            return None
    
    def create_branch(self, repo: Repository, branch_name: str, base_branch: str = None) -> bool:
        """
        Create a new branch in repository.
        
        Args:
            repo: Repository object
            branch_name: Name of new branch
            base_branch: Base branch to create from (default: default_branch)
            
        Returns:
            bool: True if successful
        """
        try:
            base_branch = base_branch or repo.default_branch
            base_sha = repo.get_branch(base_branch).commit.sha
            ref = f"refs/heads/{branch_name}"
            repo.create_git_ref(ref, base_sha)
            logger.info(f"Created branch: {branch_name}")
            return True
        except GithubException as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
    
    def commit_file(
        self,
        repo: Repository,
        file_path: str,
        file_content: str,
        commit_message: str,
        branch: str
    ) -> bool:
        """
        Commit a file to repository.
        
        Args:
            repo: Repository object
            file_path: Path to file in repo (e.g., ".github/workflows/ci.yml")
            file_content: Content of the file
            commit_message: Commit message
            branch: Branch to commit to
            
        Returns:
            bool: True if successful
        """
        try:
            try:
                # Try to get existing file
                file = repo.get_contents(file_path, ref=branch)
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=file_content,
                    sha=file.sha,
                    branch=branch
                )
                logger.info(f"Updated file: {file_path}")
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=file_content,
                    branch=branch
                )
                logger.info(f"Created file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to commit file {file_path}: {e}")
            return False
    
    def create_pull_request(
        self,
        repo: Repository,
        title: str,
        body: str,
        head: str,
        base: str
    ) -> Optional[PullRequest]:
        """
        Create a pull request.
        
        Args:
            repo: Repository object
            title: PR title
            body: PR description
            head: Head branch (feature branch)
            base: Base branch (target branch)
            
        Returns:
            PullRequest object or None if failed
        """
        try:
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            logger.info(f"Created PR: {pr.number} - {pr.title}")
            return pr
        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")
            return None
    
    def get_pull_request(self, repo: Repository, pr_number: int) -> Optional[PullRequest]:
        """
        Get pull request by number.
        
        Args:
            repo: Repository object
            pr_number: PR number
            
        Returns:
            PullRequest object or None if not found
        """
        try:
            pr = repo.get_pull(pr_number)
            return pr
        except GithubException as e:
            logger.error(f"Failed to get PR {pr_number}: {e}")
            return None
    
    def merge_pull_request(
        self,
        pr: PullRequest,
        commit_title: str = None,
        commit_message: str = None,
        merge_method: str = "squash"
    ) -> bool:
        """
        Merge a pull request.
        
        Args:
            pr: PullRequest object
            commit_title: Title for merge commit
            commit_message: Message for merge commit
            merge_method: Merge method ("merge", "squash", or "rebase")
            
        Returns:
            bool: True if successful
        """
        try:
            pr.merge(
                commit_title=commit_title,
                commit_message=commit_message,
                merge_method=merge_method
            )
            logger.info(f"Merged PR: {pr.number}")
            return True
        except GithubException as e:
            logger.error(f"Failed to merge PR {pr.number}: {e}")
            return False
    
    def cleanup_temp_dir(self, session_id: str) -> bool:
        """
        Clean up temporary directory for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if successful
        """
        return self._cleanup_temp_dir(session_id)
    
    def _cleanup_temp_dir(self, session_id: str) -> bool:
        """
        Internal method to clean up temporary directory.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if successful
        """
        if session_id not in self.temp_dirs:
            return False
        
        try:
            temp_dir = self.temp_dirs[session_id]
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            del self.temp_dirs[session_id]
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory for session {session_id}: {e}")
            return False
