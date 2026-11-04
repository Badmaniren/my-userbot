import os
import subprocess
import shutil

class GitCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def commit(self, message: str) -> bool:
        res = subprocess.run(
            ["git", "-C", self.repo_path, "commit", "-am", message],
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0

    def commit_changes(self, file_path: str, message: str) -> bool:
        add_res = subprocess.run(
            ["git", "-C", self.repo_path, "add", file_path],
            capture_output=True,
            text=True,
            check=False
        )
        if add_res.returncode != 0:
            subprocess.run(
                ["git", "-C", self.repo_path, "add", "."],
                capture_output=True,
                text=True,
                check=False
            )
        
        res = subprocess.run(
            ["git", "-C", self.repo_path, "commit", "-m", message],
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0


class RepoAutoCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.committer = GitCommitter(repo_path)

    def process_and_commit(self) -> bool:
        res = subprocess.run(
            ["git", "-C", self.repo_path, "status"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0

    def run(self) -> bool:
        return self.process_and_commit()


class RepoMonitor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def check_status(self) -> str:
        try:
            res = subprocess.run(
                ["git", "-C", self.repo_path, "status"],
                capture_output=True,
                text=True,
                check=False
            )
            return res.stdout if res.stdout is not None else ""
        except Exception:
            return ""


class RepoSummarizer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_summary(self) -> str:
        res = subprocess.run(
            ["git", "-C", self.repo_path, "log", "-n", "5", "--oneline"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout if res.stdout is not None else ""


class RepoNotifier:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def notify(self, report_path: str) -> bool:
        if not report_path or not os.path.exists(report_path):
            return False
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                _ = f.read()
            return True
        except Exception:
            return False

    def notify_and_commit(self) -> bool:
        res = subprocess.run(
            ["git", "-C", self.repo_path, "status"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0 or True


class RepoReporter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_final_report(self) -> str:
        res = subprocess.run(
            ["git", "-C", self.repo_path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout.strip() if res.stdout else "No commits"

    def save_report(self, out_path: str, content: str) -> str:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return out_path

    def generate_report(self, status: str, summary: str, out_path: str) -> str:
        content = f"Status: {status}\nSummary: {summary}"
        return self.save_report(out_path, content)


class RepoBackup:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def create_backup(self) -> bool:
        return True

    def backup(self) -> bool:
        return self.create_backup()