"""
Git Service - Handle git operations for projects
"""

import subprocess
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class GitBranch:
    name: str
    is_current: bool
    commit_sha: str
    last_commit_message: str
    last_commit_date: Optional[datetime] = None


@dataclass
class GitCommit:
    sha: str
    short_sha: str
    message: str
    author: str
    author_email: str
    date: datetime
    files_changed: int = 0


@dataclass
class GitStatus:
    is_repo: bool
    branch: Optional[str] = None
    has_changes: bool = False
    staged_files: List[str] = None
    modified_files: List[str] = None
    untracked_files: List[str] = None
    
    def __post_init__(self):
        self.staged_files = self.staged_files or []
        self.modified_files = self.modified_files or []
        self.untracked_files = self.untracked_files or []


class GitService:
    """Service for handling git operations on a repository"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        
    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the repository"""
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise GitError(f"Git command failed: {result.stderr}")
        return result
    
    def is_git_repo(self) -> bool:
        """Check if the path is a git repository"""
        result = self._run_git("rev-parse", "--is-inside-work-tree", check=False)
        return result.returncode == 0 and result.stdout.strip() == "true"
    
    def get_status(self) -> GitStatus:
        """Get the current git status"""
        if not self.is_git_repo():
            return GitStatus(is_repo=False)
        
        # Get current branch
        branch_result = self._run_git("branch", "--show-current", check=False)
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
        
        # Get status --porcelain for machine-readable output
        status_result = self._run_git("status", "--porcelain", check=False)
        
        staged_files = []
        modified_files = []
        untracked_files = []
        
        if status_result.returncode == 0:
            for line in status_result.stdout.strip().split("\n"):
                if not line:
                    continue
                status_code = line[:2]
                file_path = line[3:]
                
                # First char is staging area, second is working tree
                if status_code[0] in "MADRCU":
                    staged_files.append(file_path)
                if status_code[1] in "MADRCU":
                    modified_files.append(file_path)
                if status_code == "??":
                    untracked_files.append(file_path)
        
        has_changes = bool(staged_files or modified_files or untracked_files)
        
        return GitStatus(
            is_repo=True,
            branch=branch,
            has_changes=has_changes,
            staged_files=staged_files,
            modified_files=modified_files,
            untracked_files=untracked_files,
        )
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name"""
        result = self._run_git("branch", "--show-current", check=False)
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    
    def get_current_commit(self) -> Optional[str]:
        """Get the current commit SHA"""
        result = self._run_git("rev-parse", "HEAD", check=False)
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    
    def get_branches(self) -> List[GitBranch]:
        """Get all branches with their info"""
        if not self.is_git_repo():
            return []
        
        # Format: refname:short, objectname:short, subject, HEAD indicator
        format_str = "%(refname:short)|%(objectname:short)|%(subject)|%(HEAD)"
        result = self._run_git(
            "for-each-ref",
            "--format=" + format_str,
            "refs/heads/",
            check=False
        )
        
        if result.returncode != 0:
            return []
        
        branches = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) >= 4:
                branches.append(GitBranch(
                    name=parts[0],
                    commit_sha=parts[1],
                    last_commit_message=parts[2],
                    is_current=parts[3] == "*",
                ))
        
        return branches
    
    def get_commits(self, limit: int = 50, branch: Optional[str] = None) -> List[GitCommit]:
        """Get recent commits"""
        if not self.is_git_repo():
            return []
        
        # Format for parsing
        format_str = "%H|%h|%s|%an|%ae|%aI"
        args = [
            "log",
            f"--format={format_str}",
            f"-n{limit}",
        ]
        if branch:
            args.append(branch)
        
        result = self._run_git(*args, check=False)
        if result.returncode != 0:
            return []
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 5)
            if len(parts) >= 6:
                commits.append(GitCommit(
                    sha=parts[0],
                    short_sha=parts[1],
                    message=parts[2],
                    author=parts[3],
                    author_email=parts[4],
                    date=datetime.fromisoformat(parts[5]),
                ))
        
        return commits
    
    def stage_files(self, files: List[str]) -> None:
        """Stage files for commit"""
        if not files:
            return
        self._run_git("add", *files)
    
    def stage_all(self) -> None:
        """Stage all changes"""
        self._run_git("add", "-A")
    
    def commit(self, message: str, author: Optional[str] = None) -> GitCommit:
        """Create a commit with the staged changes"""
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])
        
        self._run_git(*args)
        
        # Get the created commit
        commits = self.get_commits(limit=1)
        if not commits:
            raise GitError("Failed to get commit after creating it")
        return commits[0]
    
    def create_branch(self, name: str, checkout: bool = False) -> None:
        """Create a new branch"""
        if checkout:
            self._run_git("checkout", "-b", name)
        else:
            self._run_git("branch", name)
    
    def checkout_branch(self, name: str) -> None:
        """Checkout an existing branch"""
        self._run_git("checkout", name)
    
    def get_file_at_commit(self, file_path: str, commit: str = "HEAD") -> Optional[str]:
        """Get file content at a specific commit"""
        result = self._run_git("show", f"{commit}:{file_path}", check=False)
        if result.returncode != 0:
            return None
        return result.stdout
    
    def diff_files(self, file_path: str, commit1: str = "HEAD", commit2: Optional[str] = None) -> str:
        """Get diff for a file between commits"""
        if commit2:
            result = self._run_git("diff", commit1, commit2, "--", file_path, check=False)
        else:
            result = self._run_git("diff", commit1, "--", file_path, check=False)
        return result.stdout
    
    def stash_changes(self, message: Optional[str] = None) -> bool:
        """Stash current changes"""
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        result = self._run_git(*args, check=False)
        return result.returncode == 0
    
    def stash_pop(self) -> bool:
        """Pop the latest stash"""
        result = self._run_git("stash", "pop", check=False)
        return result.returncode == 0
    
    def reset_file(self, file_path: str, commit: str = "HEAD") -> None:
        """Reset a file to its state at a commit"""
        self._run_git("checkout", commit, "--", file_path)
    
    def reset_hard(self, commit: str = "HEAD") -> None:
        """Hard reset to a commit"""
        self._run_git("reset", "--hard", commit)


class GitError(Exception):
    """Git operation error"""
    pass
