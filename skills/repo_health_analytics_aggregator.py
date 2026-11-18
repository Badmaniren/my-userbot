import json
import datetime
from typing import Dict, Any, List

from skills import repo_health_collector

class RepoHealthAnalyticsAggregator:
    """Агрегатор метрик здоровья репозитория."""

    def aggregate(self, repo_id: str) -> Dict[str, Any]:
        if repo_health_collector is not None and hasattr(repo_health_collector, "fetch_raw_metrics"):
            raw_metrics = repo_health_collector.fetch_raw_metrics(repo_id)
        else:
            raw_metrics = {}
        
        return {
            "repo_id": raw_metrics.get("repo_id", repo_id),
            "metrics": {
                "commits": raw_metrics.get("commits", 0),
                "issues": raw_metrics.get("issues", 0),
                "vulnerabilities": raw_metrics.get("vulnerabilities", 0),
                "status": raw_metrics.get("status", "unknown")
            },
            "aggregated_at": datetime.datetime.utcnow().isoformat()
        }

    def aggregate_from_stream(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'rb') as f:
            content = f.read()
        data = json.loads(content.decode('utf-8'))
        return data

    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        commits = metrics.get("commits", 0)
        issues = metrics.get("issues", 0)
        vulnerabilities = metrics.get("vulnerabilities", 0)
        
        score = 100.0 - (issues * 2.0) - (vulnerabilities * 10.0) + (min(commits, 100) * 0.1)
        if score < 0.0:
            return 0.0
        if score > 100.0:
            return 100.0
        return float(score)

    def aggregate_batch(self, repo_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for rid in repo_ids:
            if repo_health_collector is not None and hasattr(repo_health_collector, "fetch_raw_metrics"):
                raw_metrics = repo_health_collector.fetch_raw_metrics(rid)
            else:
                raw_metrics = {}
            results.append({
                "repo_id": rid,
                "metrics": {
                    "commits": raw_metrics.get("commits", 0),
                    "issues": raw_metrics.get("issues", 0),
                    "vulnerabilities": raw_metrics.get("vulnerabilities", 0)
                }
            })
        return results


def aggregate_repo_health_analytics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    commits = raw_data.get("commit_count", 0)
    issues = raw_data.get("open_issues", 0)
    vulnerabilities = raw_data.get("vulnerabilities", 0)

    score = 100.0 - (issues * 2.0) - (vulnerabilities * 10.0)
    if score < 0.0:
        score = 0.0

    report_path = f"report_{raw_data.get('repo_id', 'unknown')}.json"
    report_data = {
        "repo_id": raw_data.get("repo_id"),
        "aggregated_score": score,
        "metrics_summary": {
            "commit_count": commits,
            "open_issues": issues,
            "vulnerabilities": vulnerabilities
        }
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f)

    report_data["report_file_path"] = report_path
    return report_data


def collect_repo_health(repo_id: str, commit_count: int = 0, open_issues: int = 0, vulnerabilities: int = 0) -> Dict[str, Any]:
    return {
        "repo_id": repo_id,
        "commit_count": commit_count,
        "open_issues": open_issues,
        "vulnerabilities": vulnerabilities
    }