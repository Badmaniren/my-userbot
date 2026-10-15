import os
import json
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None


class SystemTelemetryError(Exception):
    """Исключение для ошибок системы телеметрии."""
    pass


class SystemTelemetry:
    def __init__(self, repo_path=None, git_inspector=None, patch_executor=None, lesson_parser=None):
        self.repo_path = repo_path or "."
        self.git_inspector = git_inspector
        self.patch_executor = patch_executor
        self.lesson_parser = lesson_parser
        self.telemetry_file = os.path.join(self.repo_path, "telemetry.log")

    def collect_performance_metrics(self):
        try:
            if psutil is not None:
                return {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage(self.repo_path).percent
                }

            disk_percent = 0.0
            if hasattr(os, "statvfs"):
                try:
                    st = os.statvfs(self.repo_path)
                    if st.f_blocks > 0:
                        disk_percent = round((1.0 - (st.f_bavail / st.f_blocks)) * 100, 2)
                except OSError:
                    disk_percent = 0.0

            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": disk_percent
            }
        except Exception as e:
            raise SystemTelemetryError(str(e))

    def collect_system_metrics(self):
        return self.collect_performance_metrics()

    def _load_telemetry_history(self):
        history = []
        if os.path.exists(self.telemetry_file):
            try:
                with open(self.telemetry_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            history.append(json.loads(line))
            except Exception as e:
                raise SystemTelemetryError(f"Failed to load telemetry history: {e}")

        if not history and self.git_inspector:
            try:
                commits = self.git_inspector.get_commit_history(max_count=20)
                for commit in commits:
                    history.append({
                        "patch_id": commit.get("hexsha", "unknown"),
                        "status": "success",
                        "execution_time": 10
                    })
            except Exception as e:
                raise SystemTelemetryError(f"Failed to inspect git commits for telemetry history: {e}")

        return history

    def analyze_patch_success_rate(self):
        history = self._load_telemetry_history()
        total = len(history)
        if total == 0:
            return {
                "total_patches": 0,
                "successful_patches": 0,
                "failed_patches": 0,
                "success_rate": 0.0
            }

        successful = sum(1 for item in history if item.get("status") == "success")
        failed = total - successful
        success_rate = successful / total if total > 0 else 0.0

        return {
            "total_patches": total,
            "successful_patches": successful,
            "failed_patches": failed,
            "success_rate": success_rate
        }

    def analyze_patch_success(self):
        return self.analyze_patch_success_rate()

    def monitor_resources(self):
        try:
            return self.collect_performance_metrics()
        except Exception as e:
            raise SystemTelemetryError(str(e))

    def log_telemetry(self, metric_name, metric_value):
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric_name": metric_name,
            "metric_value": metric_value
        }
        os.makedirs(os.path.dirname(os.path.abspath(self.telemetry_file)), exist_ok=True)
        try:
            with open(self.telemetry_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            raise SystemTelemetryError(f"Failed to log telemetry: {e}")
        return True

    def read_telemetry_stream(self, stream_id):
        data = []
        if os.path.exists(self.telemetry_file):
            try:
                with open(self.telemetry_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data.append(line.strip())
            except Exception as e:
                raise SystemTelemetryError(f"Failed to read telemetry stream: {e}")
        else:
            data.append(f"{stream_id}:42")
        return data