import json
import time
import io
from pathlib import Path
from contextlib import contextmanager

class TelemetryError(Exception):
    """Кастомное исключение для ошибок телеметрии."""
    pass

class CycleTracker:
    def __init__(self, telemetry, cycle_id):
        self.telemetry = telemetry
        self.cycle_id = cycle_id
        self.status = "UNKNOWN"
        self.start_time = 0.0

    def set_status(self, status):
        self.status = status

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        exec_time = time.time() - self.start_time
        if exc_type is not None:
            self.status = "FAILED"
        self.telemetry.record_cycle_manual(self.cycle_id, exec_time, self.status)

class ExecutionTracker:
    def __init__(self, telemetry, key):
        self.telemetry = telemetry
        self.key = key
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        exec_time = time.time() - self.start_time
        success = exc_type is None
        self.telemetry.metrics[self.key] = {
            "success": success,
            "execution_time": exec_time
        }

class SystemTelemetry:
    def __init__(self, repo_path=None, session_id=None):
        self.repo_path = repo_path
        self.session_id = session_id
        self.metrics = {
            "cycles": [],
            "patches": [],
            "errors": []
        }

    def get_metrics(self):
        return self.metrics

    def track_cycle(self, cycle_id):
        return CycleTracker(self, cycle_id)

    def track_execution(self, key):
        return ExecutionTracker(self, key)

    def record_cycle_manual(self, cycle_id, execution_time, status):
        self.metrics["cycles"].append({
            "cycle_id": cycle_id,
            "execution_time": execution_time,
            "status": status
        })

    def record_patch(self, patch_id, file_path, success, lines_delta):
        self.metrics["patches"].append({
            "patch_id": patch_id,
            "file_path": file_path,
            "success": success,
            "lines_delta": lines_delta
        })

    def log_critical_error(self, error, context=None):
        error_entry = {
            "message": str(error),
            "context": context if context is not None else {},
            "timestamp": time.time()
        }
        self.metrics["errors"].append(error_entry)

    def export_telemetry(self, export_path):
        data = json.dumps(self.metrics, ensure_ascii=False, indent=2)
        if hasattr(export_path, "write"):
            if isinstance(export_path, io.BytesIO) or getattr(export_path, "mode", "").find("b") != -1:
                export_path.write(data.encode("utf-8"))
            else:
                export_path.write(data)
        else:
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(data)

    def load_from_disk(self, file_path):
        if hasattr(file_path, "read"):
            content = file_path.read()
        else:
            p = Path(file_path)
            if not p.exists() or p.stat().st_size == 0:
                raise TelemetryError("Empty telemetry file or corrupted stream")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError as e:
                raise TelemetryError(f"Corrupted stream: {e}") from e

        if not content or not content.strip():
            raise TelemetryError("Empty telemetry file or corrupted stream")

        try:
            self.metrics = json.loads(content)
        except json.JSONDecodeError as e:
            raise TelemetryError(f"Invalid JSON payload: {e}") from e


class TelemetryCollector:
    def __init__(self):
        self.sessions = []

    def add_session(self, telemetry_instance):
        self.sessions.append(telemetry_instance)

    def aggregate_summary(self):
        total_sessions = len(self.sessions)
        total_cycles = 0
        total_exec_time = 0.0

        for session in self.sessions:
            cycles = session.get_metrics().get("cycles", [])
            total_cycles += len(cycles)
            for c in cycles:
                total_exec_time += c.get("execution_time", 0.0)

        avg_time = (total_exec_time / total_cycles) if total_cycles > 0 else 0.0

        return {
            "total_sessions": total_sessions,
            "total_cycles": total_cycles,
            "average_execution_time": avg_time
        }