import os
import time
import json
import logging
import threading
from contextlib import contextmanager
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger("SystemTelemetry")

class SystemTelemetryError(Exception):
    """Исключение для ошибок системы телеметрии."""
    pass

class SystemTelemetry:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path
        self.start_time = time.time()
        self.metrics_cache = {}
        self._timers = {}

    def log_evolution_cycle(self, cycle_id, metrics):
        logger.info(f"Evolution cycle {cycle_id} finished with metrics: {metrics}")

    def collect_system_metrics(self):
        try:
            if psutil is None:
                return {"cpu_usage": 0.0, "memory_usage": 0.0}
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            return {"cpu_usage": cpu, "memory_usage": mem}
        except Exception as e:
            raise SystemTelemetryError(f"Failed to collect system metrics: {e}")

    def monitor_engine_health(self):
        try:
            if psutil is None:
                cpu = 0.0
                mem = 0.0
            else:
                cpu = float(psutil.cpu_percent(interval=0.1))
                mem = float(psutil.virtual_memory().percent)
        except Exception as e:
            raise SystemTelemetryError(f"Failed to monitor engine health: {e}")

        uptime = time.time() - self.start_time
        active_threads = threading.active_count()
        repo_status = "active" if self.repo_path and os.path.exists(self.repo_path) else "unknown"

        return {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "uptime": uptime,
            "active_threads": active_threads,
            "repo_status": repo_status
        }

    def dump_telemetry_report(self, filename):
        report = {
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time,
            "metrics": self.metrics_cache
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        return filename

    @contextmanager
    def track_execution(self, operation_name):
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            logger.debug(f"Operation '{operation_name}' executed in {duration:.4f} seconds")

    def log_metric(self, key, value):
        self.metrics_cache[key] = value

    def get_metrics(self):
        return self.metrics_cache

    def start_timer(self, name):
        self._timers[name] = time.time()

    def stop_timer(self, name):
        start = self._timers.pop(name, time.time())
        return time.time() - start

    def check_system_health(self):
        return self.monitor_engine_health()