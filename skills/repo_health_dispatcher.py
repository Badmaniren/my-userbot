from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_notifier import RepoNotifier


class RepoHealthDispatcher:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo_health_dashboard = RepoHealthDashboard(repo_path)
        self.repo_notifier = RepoNotifier(repo_path)

    def dispatch_health_and_notify(self, file_path: str) -> bool:
        dashboard = RepoHealthDashboard(self.repo_path)
        data = dashboard.generate_dashboard()
        exported = dashboard.export_dashboard(file_path)
        
        if not exported:
            return False

        notifier = RepoNotifier(self.repo_path)
        return notifier.notify(file_path)

    def process_stream_and_dispatch(self, stream, file_path: str) -> bool:
        dashboard = RepoHealthDashboard(self.repo_path)
        dashboard.process_stream(stream)
        dashboard.export_dashboard(file_path)

        notifier = RepoNotifier(self.repo_path)
        return notifier.notify(file_path)

    def check_and_notify_critical(self, title: str, value, file_path: str) -> bool:
        dashboard = RepoHealthDashboard(self.repo_path)
        widget_str = dashboard.render_widget(title, value)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(widget_str)

        notifier = RepoNotifier(self.repo_path)
        return notifier.notify_and_commit()

    def dispatch(self):
        return self.dispatch_health_and_notify(f"{self.repo_path}/report.json")