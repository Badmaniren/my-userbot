import time
from collections import deque

class SystemHealthTracker:
    def __init__(self, max_records=None):
        self.max_records = max_records
        self.metrics = {}
        self.errors = []
        self.memory_metrics = {}

    def record_execution_time(self, op_name, duration):
        if op_name not in self.metrics:
            self.metrics[op_name] = deque(maxlen=self.max_records)
        self.metrics[op_name].append((time.time(), duration, {"type": "execution_time"}))

    def record_resource_consumption(self, res_name, cpu_percent=None, memory_mb=None):
        if res_name not in self.metrics:
            self.metrics[res_name] = deque(maxlen=self.max_records)
        self.metrics[res_name].append((time.time(), cpu_percent, {"type": "resource"}))
        if memory_mb is not None:
            self.memory_metrics[res_name] = memory_mb

    def record_error(self, err_type, err_msg):
        self.errors.append((time.time(), err_type, err_msg))

    def get_average_metric(self, metric_name):
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return 0.0
        values = [val for _, val, _ in self.metrics[metric_name] if val is not None]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def get_error_frequency(self, window):
        if window <= 0.0:
            return 0.0
        now = time.time()
        cutoff = now - window
        count = sum(1 for t, _, _ in self.errors if t >= cutoff)
        return count / window

    def analyze_stability(self):
        total_errors = len(self.errors)
        if total_errors <= 10:
            status = "HEALTHY"
        elif total_errors <= 50:
            status = "WARNING"
        else:
            status = "CRITICAL"

        averages = {name: self.get_average_metric(name) for name in self.metrics}
        return {
            "status": status,
            "total_errors": total_errors,
            "averages": averages
        }

    def get_aggregated_metrics(self):
        components = set(self.metrics.keys()) | set(self.memory_metrics.keys()) | {err[1] for err in self.errors}

        summary = {}
        for comp in components:
            comp_summary = {
                "last_execution_time": None,
                "cpu_percent": None,
                "memory_mb": None,
                "error_count": 0
            }

            if comp in self.metrics:
                exec_times = [val for _, val, tags in self.metrics[comp] if tags.get("type") == "execution_time" and val is not None]
                if exec_times:
                    comp_summary["last_execution_time"] = exec_times[-1]

                cpu_values = [val for _, val, tags in self.metrics[comp] if tags.get("type") == "resource" and val is not None]
                if cpu_values:
                    comp_summary["cpu_percent"] = cpu_values[-1]

            if comp in self.memory_metrics:
                comp_summary["memory_mb"] = self.memory_metrics[comp]

            comp_summary["error_count"] = sum(1 for _, err_type, _ in self.errors if err_type == comp)

            summary[comp] = comp_summary

        return summary