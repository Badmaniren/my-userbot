import io
import json
import os

from skills.repo_health_collector import collect_repo_health_metrics
from skills.repo_health_trend_calculator import calculate_repo_health_trends

class RepoHealthAnalyticsReporter:
    def generate_report(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary")
        
        required_keys = ["repository", "metrics", "status", "timestamp"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")
        
        metrics = data["metrics"]
        if not isinstance(metrics, dict) or not metrics:
            raise ValueError("Metrics must be a non-empty dictionary")
            
        calculated_score = sum(v for v in metrics.values() if isinstance(v, (int, float)))
        
        return {
            "summary": {
                "status": data["status"],
                "timestamp": data["timestamp"]
            },
            "details": {
                "repository": data["repository"],
                "metrics": metrics
            },
            "analytics": {
                "calculated_score": calculated_score
            }
        }

    def export_report(self, report_data: dict, file_path: str, format: str = "json") -> str:
        if format.lower() != "json":
            raise ValueError(f"Unsupported format: {format}")
            
        content = json.dumps(report_data, ensure_ascii=False)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def export_to_stream(self, report_data: dict, format: str = "bytes") -> io.BytesIO:
        stream = io.BytesIO()
        content = json.dumps(report_data, ensure_ascii=False).encode("utf-8")
        stream.write(content)
        stream.seek(0)
        return stream


def generate_and_export_repo_health_analytics_report(
    repo_id: str,
    collected_metrics: dict,
    trend_analysis: dict,
    destination_file: str
) -> dict:
    reporter = RepoHealthAnalyticsReporter()
    
    report_input = {
        "repository": repo_id,
        "metrics": collected_metrics.get("metrics", {}),
        "status": collected_metrics.get("status", "HEALTHY"),
        "timestamp": collected_metrics.get("timestamp", 1600000000)
    }
    
    report_data = reporter.generate_report(report_input)
    report_data["trend_analysis"] = trend_analysis
    
    reporter.export_report(report_data, destination_file, format="json")
    
    return {
        "success": True,
        "repo_id": repo_id,
        "destination_file": destination_file
    }