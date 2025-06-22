from typing import Optional

import git


class GitRepo:
    """A wrapper around a GitPython repository."""

    def __init__(self, path: str):
        try:
            self.repo = git.Repo(path, search_parent_directories=True)
            print("Successfully loaded Git repository at: " f"{self.repo.working_dir}")
        except git.InvalidGitRepositoryError:
            print(
                f"No Git repository found at path: {path}. " "Initializing a new one."
            )
            self.repo = git.Repo.init(path)
        except Exception as e:
            print(f"An unexpected error occurred with Git: {e}")
            self.repo = None

    def get_status(self) -> Optional[str]:
        """Returns the output of 'git status --porcelain'."""
        if not self.repo:
            return None
        return self.repo.git.status(porcelain=True)

    def add_all(self):
        """Stages all changes."""
        if self.repo:
            self.repo.git.add(A=True)

    def commit(self, message: str) -> Optional[git.Commit]:
        """Creates a new commit."""
        if self.repo and self.repo.is_dirty(untracked_files=True):
            self.add_all()
            return self.repo.index.commit(message)
        return None

    def get_diff(self, commit: Optional[str] = "HEAD") -> Optional[str]:
        """Returns the diff for the specified commit, or the staged diff."""
        if not self.repo:
            return None

        target = commit if commit != "STAGED" else None
        return self.repo.git.diff(target)

    def get_tracked_files(self) -> list:
        """Returns a list of all tracked files in the repository."""
        if not self.repo:
            return []

        try:
            # Use git ls-files to get all tracked files
            tracked_files = self.repo.git.ls_files().splitlines()
            return tracked_files
        except Exception as e:
            print(f"Error getting tracked files: {e}")
            return []
