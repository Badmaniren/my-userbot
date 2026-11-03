from skills.repo_monitor import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.git_committer import GitCommitter


class RepoAutoCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.monitor = RepoMonitor(repo_path)

    def run(self) -> bool:
        status = self.monitor.check_status()
        if not status or not status.strip():
            return False

        summarizer = RepoSummarizer(self.repo_path)
        committer = GitCommitter(self.repo_path)

        summary = summarizer.generate_summary()
        result = committer.commit(summary)
        return bool(result)