import json
import os
import pathlib
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from skills.repo_monitor import repo_monitor
from skills.repo_auditor import repo_auditor
from skills.repo_analytics import repo_analytics
from skills.repo_logger import repo_logger


class RepoHealthDegradationError(Exception):
    """Исключение, вызываемое при сильной деградации здоровья репозитория или сбое сбора метрик."""
    pass


@dataclass
class RepoHealthMetric:
    name: str
    value: float
    details: Dict[str, Any] = field(default_factory=dict)


class RepoHealthPulseCollector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def collect_metric(self, metric_name: str) -> RepoHealthMetric:
        cmd = ["echo", json.dumps({"metric": metric_name, "value": 42.0, "details": {}})]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout = res.stdout
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8')

        if res.returncode != 0:
            err_output = res.stderr.decode('utf-8') if isinstance(res.stderr, bytes) else res.stderr
            raise RepoHealthDegradationError(err_output)

        try:
            data = json.loads(stdout.strip())
            return RepoHealthMetric(
                name=data.get("metric", metric_name),
                value=float(data.get("value", 0.0)),
                details=data.get("details", {})
            )
        except Exception as e:
            if res.returncode != 0:
                raise RepoHealthDegradationError(str(e))
            return RepoHealthMetric(name=metric_name, value=0.0, details={})

    def parse_health_stream(self, stream_name: str) -> Dict[str, Any]:
        result = {}
        file_path = pathlib.Path(self.repo_path) / stream_name
        with open(file_path, "rb") as f:
            for line in f:
                line_str = line.decode('utf-8').strip()
                if ":" in line_str:
                    k, v = line_str.split(":", 1)
                    try:
                        result[k.strip()] = int(v.strip())
                    except ValueError:
                        try:
                            result[k.strip()] = float(v.strip())
                        except ValueError:
                            result[k.strip()] = v.strip()
        return result

    def enforce_health_guard(self, threshold: float) -> None:
        metric = self.collect_metric("guard_metric")
        if metric.value > threshold:
            raise RepoHealthDegradationError(f"Health threshold exceeded: {metric.value} > {threshold}")


class RepoHealthTrendAnalyzer:
    def analyze_trend(self, metrics: List[RepoHealthMetric]) -> bool:
        if not metrics or len(metrics) < 2:
            return False
        
        values = [m.value for m in metrics]
        history = values[:-1]
        latest = values[-1]
        avg_history = sum(history) / len(history) if history else 0.0
        
        if latest - avg_history > 40.0:
            return True
            
        increasing_steps = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        if increasing_steps >= len(values) * 0.8 and (values[-1] - values[0] > 30.0):
            return True

        return False


def repo_health_pulse(repo_path: str, analytics: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    status = "healthy"
    score = analytics.get("analytics_score", 50)
    if score < 20:
        status = "critical"
    elif score < 50:
        status = "degraded"

    output_data = {
        "status": status,
        "run_id": run_id,
        "analytics": analytics
    }

    report_file_path = pathlib.Path(repo_path) / f"health_report_{run_id}.json"
    report_file_path.write_text(json.dumps(output_data))

    return output_data