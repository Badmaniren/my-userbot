import subprocess
from skills.repo_monitor import RepoMonitor, GitCommitter


class RepoSummarizer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_summary(self) -> str:
        try:
            monitor = RepoMonitor(self.repo_path)
            status = monitor.check_status()
        except Exception as e:
            return f"Error checking status: {str(e)}"

        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "log", "-n", "5", "--stat", "--oneline"],
                capture_output=True,
                check=True
            )
            git_output = result.stdout.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Status: {status}\nGit command failed: {str(e)}"

        return f"Status: {status}\nRecent commits and changes:\n{git_output}"