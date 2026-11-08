import os
import json
import requests
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

class PulseException(Exception):
    """Исключение для ошибок пульса репозитория."""
    pass

@dataclass
class PulseMetric:
    repo_id: str
    name: str
    value: Optional[float] = None
    is_healthy: bool = True
    error_message: str = ""

class RepoMonitor:
    def check_status(self, repo_path: str) -> Dict[str, Any]:
        return {"status": "ok", "path": repo_path}

class RepoLogger:
    def log_event(self, target_file: str, message: str) -> bool:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(message + "\n")
        return True

class RepoAnalytics:
    def generate_metrics_report(self, repo_path: str) -> Dict[str, Any]:
        return {"report": "generated", "path": repo_path}

class RepoHealthPulseEngine:
    def __init__(self, source_path: str = ""):
        self.source_path = source_path

    def _fetch_raw_metric(self, repo_id: str, name: str) -> float:
        return 0.0

    def collect_metric(self, repo_id: str, name: str) -> PulseMetric:
        try:
            value = self._fetch_raw_metric(repo_id, name)
            return PulseMetric(repo_id=repo_id, name=name, value=value, is_healthy=True)
        except Exception as e:
            return PulseMetric(repo_id=repo_id, name=name, value=None, is_healthy=False, error_message=str(e))

    def monitor_stream(self, stream_path: str, limit: int = 5) -> List[str]:
        metrics = []
        with open(stream_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                metrics.append(line.strip())
        return metrics

    def export_pulse(self, url: str, payload: dict) -> dict:
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            raise PulseException(str(e))

    def collect_and_process_pulse(self, repo_path: str, run_id: str, metric: Any) -> Dict[str, Any]:
        return {
            "status": "success",
            "run_id": run_id,
            "metric": metric,
            "repo_path": repo_path
        }

    def process_stream(self, source: Optional[Any] = None) -> List[Dict[str, Any]]:
        target = source if source is not None else self.source_path
        results = []
        if not target:
            return results

        if hasattr(target, "readlines"):
            lines = target.readlines()
        elif hasattr(target, "read"):
            lines = target.read().splitlines()
        elif isinstance(target, str):
            if os.path.exists(target):
                with open(target, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            else:
                lines = target.strip().splitlines()
        elif isinstance(target, (list, tuple)):
            for item in target:
                if isinstance(item, str):
                    try:
                        results.append(json.loads(item))
                    except Exception:
                        pass
                elif isinstance(item, dict):
                    results.append(item)
            return results
        else:
            return results

        for line in lines:
            line_str = line.decode("utf-8") if isinstance(line, bytes) else str(line).strip()
            if line_str:
                try:
                    results.append(json.loads(line_str))
                except Exception:
                    pass
        return results


class PulseEngine(RepoHealthPulseEngine):
    pass