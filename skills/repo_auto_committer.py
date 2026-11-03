from skills.repo_monitor import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.git_committer import GitCommitter


class RepoAutoCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.monitor = RepoMonitor(repo_path)
        self.summarizer = RepoSummarizer(repo_path)
        self.committer = GitCommitter(repo_path)

    def run(self) -> bool:
        status = self.monitor.check_status()
        if not status:
            return False
        
        summary = self.summarizer.generate_summary()
        return self.committer.commit(summary)

    def process_and_commit(self) -> bool:
        return self.run()