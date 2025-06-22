from typing import Optional

import git


class GitRepo:
    """A wrapper around a GitPython repository."""

    def __init__(self, path: str, init_new: bool = True):
        self.repo_path = path
        try:
            self.repo = git.Repo(path, search_parent_directories=True)
            print("Successfully loaded Git repository at: " f"{self.repo.working_dir}")
        except git.InvalidGitRepositoryError:
            if init_new:
                print(
                    f"No Git repository found at path: {path}. " "Initializing a new one."
                )
                self.repo = git.Repo.init(path)
            else:
                self.repo = None
                raise
        except Exception as e:
            print(f"An unexpected error occurred with Git: {e}")
            self.repo = None

    def get_status(self) -> Optional[str]:
        """Returns the output of 'git status --porcelain'."""
        if not self.repo:
            return None
        try:
            return self.repo.git.status(porcelain=True)
        except git.GitCommandError as e:
            print(f"Error getting git status: {e}")
            return None

    def add_all(self):
        """Stages all changes."""
        if self.repo:
            self.repo.git.add(A=True)

    def add_files(self, files: list):
        """Stages specific files."""
        if self.repo and files:
            for file in files:
                self.repo.git.add(file)

    def commit(self, message: str) -> Optional[str]:
        """Creates a new commit and returns its SHA."""
        if self.repo and self.repo.is_dirty(untracked_files=True):
            self.add_all()
            commit = self.repo.index.commit(message)
            return commit.hexsha
        return None

    def get_diff(self, commit: Optional[str] = "HEAD", staged: bool = True) -> Optional[str]:
        """Returns the diff for the specified commit, or the staged/unstaged diff."""
        if not self.repo:
            return None

        if not staged:
            return self.repo.git.diff()

        target = commit if commit != "STAGED" else None
        return self.repo.git.diff(target, cached=True)

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
