import json
import requests
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor
from skills.dependency_audit_aggregator import DependencyAuditAggregator
from skills.repo_reporter import RepoReporter


def start_new(target_url, repo_id, config):
    payload = dict(config)
    payload["repo_id"] = repo_id
    response = requests.post(target_url, json=payload)
    return response.json()


class RepoHealthAggregator:
    def aggregate_health_data(self, run_id, audit_info, monitoring_data, dependency_metrics):
        return {
            "run_id": run_id,
            "health_score": audit_info.get("health_score") if isinstance(audit_info, dict) else None,
            "audit_info": audit_info,
            "monitoring_data": monitoring_data,
            "dependency_metrics": dependency_metrics
        }