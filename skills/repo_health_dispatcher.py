import io
import os
from typing import Union
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
        self.repo_health_dashboard.generate_dashboard()
        if self.repo_health_dashboard.export_dashboard(file_path):
            return self._notify_with_retry(self.repo_notifier.notify, file_path)
        return False

    def process_stream_and_dispatch(self, stream_data: Union[str, io.BytesIO], file_path: str) -> bool:
        if isinstance(stream_data, str):
            stream = io.BytesIO(stream_data.encode("utf-8"))
        else:
            stream = stream_data
        
        self.repo_health_dashboard.process_stream(stream)
        if self.repo_health_dashboard.export_dashboard(file_path):
            return self._notify_with_retry(self.repo_notifier.notify, file_path)
        return False

    def check_and_notify_critical(self, title: str, value: int, file_path: str) -> bool:
        rendered_widget = self.repo_health_dashboard.render_widget(title, value)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rendered_widget)
        return self._notify_with_retry(self.repo_notifier.notify_and_commit)

    def dispatch(self) -> bool:
        expected_report_path = os.path.join(self.repo_path, "report.json")
        return self.dispatch_health_and_notify(expected_report_path)