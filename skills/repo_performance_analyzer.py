import os
import uuid
import json

from skills.repo_monitor import repo_monitor
from skills.repo_analytics import repo_analytics

class RepoPerformanceAnalyzer:
    def analyze_metric_stream(self, log_id: str, threshold: float) -> dict:
        metric_name = None
        value = 0.0
        
        with open(log_id, 'r', encoding='utf-8') as f:
            content = f.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            content = content.strip()
            if content and content.startswith("METRIC:"):
                parts = content.split(':')
                if len(parts) >= 4:
                    metric_name = parts[1]
                    try:
                        value = float(parts[2])
                    except ValueError:
                        value = 0.0

        is_bottleneck = value > threshold if metric_name is not None else False
        return {
            'log_id': log_id,
            'metric_name': metric_name,
            'value': value if metric_name is not None else 0.0,
            'is_bottleneck': is_bottleneck
        }

    def aggregate_performance(self, log_id: str) -> dict:
        total_metrics = 0
        max_val = 0.0
        
        with open(log_id, 'r', encoding='utf-8') as f:
            for line in f:
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='ignore')
                if ':' in line:
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        try:
                            val = float(parts[1])
                            total_metrics += 1
                            if val > max_val:
                                max_val = val
                        except ValueError:
                            pass

        return {
            'total_metrics_analyzed': total_metrics,
            'max_value': max_val
        }

    def _fetch_historical_data(self, metric_id: str) -> float:
        return 0.0

    def detect_regression(self, metric_id: str, current_value: float) -> tuple:
        baseline = self._fetch_historical_data(metric_id)
        diff = current_value - baseline
        is_regressed = diff > 0
        return is_regressed, diff

def repo_performance_analyzer(analyzer_input: dict) -> dict:
    repo_id = analyzer_input.get("repo_id")
    analytics_data = analyzer_input.get("analytics_data", {})
    threshold = analyzer_input.get("threshold", 0.0)
    target_path = analytics_data.get("monitoring_payload", {}).get("target_path")

    bottlenecks_identified = []
    if threshold > 0:
        bottlenecks_identified.append({"repo_id": repo_id, "threshold": threshold})

    report = {
        "analysis_id": str(uuid.uuid4()),
        "repo_id": repo_id,
        "bottlenecks_identified": bottlenecks_identified
    }

    if target_path and os.path.exists(target_path):
        report_file_path = os.path.join(target_path, f"perf_report_{repo_id}.json")
        with open(report_file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f)

    return report