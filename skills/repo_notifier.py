from skills.repo_reporter import RepoReporter
from skills.repo_auto_committer import RepoAutoCommitter


class RepoNotifier:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.reporter = RepoReporter(repo_path)
        self.committer = RepoAutoCommitter(repo_path)

    def notify(self, report_file_path: str) -> bool:
        report_content = self.reporter.generate_final_report()
        self.reporter.save_report(report_file_path, report_content)
        commit_result = self.committer.process_and_commit()
        return commit_result

    def notify_and_commit(self) -> bool:
        default_report_path = f"{self.repo_path}/report.txt"
        return self.notify(default_report_path)