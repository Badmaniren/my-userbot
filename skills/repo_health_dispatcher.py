import io
import os
from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_notifier import RepoNotifier


class RepoHealthDispatcher:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo_health_dashboard = RepoHealthDashboard(repo_path)
        self.repo_notifier = RepoNotifier(repo_path)

    def _notify_with_retry(self, notify_func, *args, **kwargs) -> bool:
        max_retries = 3
        for _ in range(max_retries):
            if notify_func(*args, **kwargs):
                return True
        return False

    def dispatch_health_and_notify(self, file_path: str) -> bool:
        self.repo_health_dashboard.generate