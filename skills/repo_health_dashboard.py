import json
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor

class RepoHealthDashboard:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_dashboard(self) -> dict:
        auditor = RepoAuditor(self.repo_path)
        if hasattr(auditor, "calculate_metrics"):
            return auditor.calculate_metrics()
        elif hasattr(auditor, "audit"):
            res = auditor.audit()
            if isinstance(res, dict):
                return res
            return {"audit_result": res}
        return {}

    def export_dashboard(self, file_path: str) -> bool:
        monitor = RepoMonitor(self.repo_path)
        status = monitor.check_status()
        
        data = self.generate_dashboard()
        data["repo_status"] = status
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return True

    def process_stream(self, stream) -> dict:
        if isinstance(stream, dict):
            return stream
        if hasattr(stream, "read"):
            raw = stream.read()
            if isinstance(raw, bytes):
                content = raw.decode("utf-8", errors="ignore")
            else:
                content = str(raw)
        elif isinstance(stream, bytes):
            content = stream.decode("utf-8", errors="ignore")
        elif isinstance(stream, str):
            content = stream
        else:
            return {"raw": stream}

        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        result = {}
        for line in content.splitlines():
            parts = line.split(":")
            if len(parts) >= 3:
                key, val = parts[1], parts[2]
                result[key] = val
            elif len(parts) == 2:
                result[parts[0]] = parts[1]
            else:
                result["raw"] = content
        return result

    def render_widget(self, title: str, value) -> str:
        return f"<div class='widget'><h3>{title}</h3><p>{value}</p></div>"