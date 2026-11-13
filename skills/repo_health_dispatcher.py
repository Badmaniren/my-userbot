import io
import os
from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_notifier import RepoNotifier


class RepoHealthDispatcher:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo_health_dashboard = RepoHealthDashboard(repo_path)
        self.repo_notifier = RepoNotifier(repo_path)

    def dispatch_health_and_notify(self, file_path: str) -> bool:
        self.repo_health_dashboard.generate_dashboard()
        exported = self.repo_health_dashboard.export_dashboard(file_path)

        if not exported:
            return False

        return self.repo_notifier.notify(file_path)

    def process_stream_and_dispatch(self, stream, file_path: str) -> bool:
        if isinstance(stream, str):
            stream = io.BytesIO(stream.encode("utf-8"))
        self.repo_health_dashboard.process_stream(stream)
        self.repo_health_dashboard.export_dashboard(file_path)

        return self.repo_notifier.notify(file_path)

    def check_and_notify_critical(self, title: str, value, file_path: str) -> bool:
        widget_str = self.repo_health_dashboard.render_widget(title, value)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(widget_str)

        return self.repo_notifier.notify_and_commit()

    def dispatch(self) -> bool:
        return self.dispatch_health_and_notify(
            os.path.join(self.repo_path, "report.json")
        )