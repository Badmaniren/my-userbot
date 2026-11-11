import json
import os

try:
    from skills.repo_auditor import RepoAuditor
except ImportError:
    RepoAuditor = None

try:
    from skills.repo_monitor import RepoMonitor
except ImportError:
    RepoMonitor = None


class RepoHealthDashboard:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_dashboard(self) -> dict:
        auditor = RepoAuditor(self.repo_path) if RepoAuditor else None
        if auditor is not None:
            if hasattr(auditor, "calculate_metrics"):
                return auditor.calculate_metrics()
            elif hasattr(auditor, "audit"):
                res = auditor.audit()
                if isinstance(res, dict):
                    return res
                else:
                    return {"audit_result": res}
        return {}

    def export_dashboard(self, file_path: str) -> bool:
        data = self.generate_dashboard()
        
        status = ""
        if RepoMonitor:
            try:
                monitor = RepoMonitor(self.repo_path)
            except TypeError:
                monitor = RepoMonitor()
            if hasattr(monitor, "check_status"):
                status = monitor.check_status()
        
        if not status:
            monitor_file_path = os.path.join(self.repo_path, "monitor_state.txt")
            if os.path.exists(monitor_file_path):
                status = monitor_file_path

        if status:
            data["repo_status"] = status

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return True
        except Exception:
            return False

    def process_stream(self, stream) -> dict:
        try:
            content = stream.read().decode('utf-8').strip()
        except Exception:
            return {}

        if not content:
            return {}

        line = content.splitlines()[0] if content.splitlines() else content
        parts = line.split(':')

        if len(parts) >= 3:
            return {parts[1]: parts[2]}
        elif len(parts) == 2:
            return {parts[0]: parts[1]}
        else:
            return {"raw": line}

    def render_widget(self, title: str, value) -> str:
        return f"<div class='widget'><h3>{title}</h3><p>{value}</p></div>"