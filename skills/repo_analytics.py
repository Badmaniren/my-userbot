import subprocess
import os

class GitCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def commit(self, message: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-am", message],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def commit_changes(self, file_path: str, message: str) -> bool:
        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            subprocess.run(
                ["git", "-C", self.repo_path, "add", rel_path],
                capture_output=True,
                text=True,
                check=True
            )
            result = subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except Exception:
            return False


class RepoAutoCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def process_and_commit(self) -> bool:
        try:
            committer = GitCommitter(self.repo_path)
            return committer.commit("Auto-commit updates")
        except Exception:
            return False

    def run(self) -> bool:
        try:
            return self.process_and_commit()
        except Exception:
            return False


class RepoMonitor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def check_status(self) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "status"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except Exception as e:
            return str(e)


class RepoSummarizer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_summary(self) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "log", "-n", "5", "--oneline"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except Exception as e:
            return str(e)