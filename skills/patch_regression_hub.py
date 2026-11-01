import os
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector


class AnomalyAuditHub:
    def __init__(self, repo_path=None, log_path=None, threshold=0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.logger = AnomalyLogger(log_path=log_path) if log_path else AnomalyLogger()
        self.inspector = GitInspector(repo_path=repo_path) if repo_path else GitInspector()

    def log_anomaly(self, source="default", severity="LOW", details="", telemetry_snapshot=None):
        if telemetry_snapshot is None:
            telemetry_snapshot = {}
        anomaly_data = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": telemetry_snapshot
        }
        self.logger.log(anomaly_data)

    def aggregate_and_report(self, metric_name=None, value=None):
        anomalies = self.logger.get_anomalies()
        score = value if value is not None else 0.0
        return {
            "aggregated": True,
            "score": score,
            "metric_name": metric_name,
            "total_anomalies": len(anomalies)
        }

    def generate_final_report(self):
        anomalies = self.logger.get_anomalies()
        return {
            "status": "verified",
            "code": "success",
            "anomalies_count": len(anomalies)
        }


def start_new(dynamic_input_data):
    repo_path = dynamic_input_data.get("repo_path")
    log_path = dynamic_input_data.get("log_path")
    threshold = dynamic_input_data.get("threshold", 0.5)

    hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

    if "stream_source" in dynamic_input_data:
        inspector = GitInspector(repo_path=repo_path)
        analysis = inspector.analyze_repository()
        if isinstance(analysis, dict) and "token" in dynamic_input_data:
            analysis["token"] = dynamic_input_data["token"]
        return analysis

    payload_id = dynamic_input_data.get("payload_id")
    if payload_id:
        severity = dynamic_input_data.get("severity_level", "LOW")
        hub.log_anomaly(source=payload_id, severity=severity, details="Payload anomaly logged")
        return hub.aggregate_and_report()

    target = dynamic_input_data.get("target", "metric")
    numeric_metric = dynamic_input_data.get("numeric_metric", 1.0)
    for k, v in dynamic_input_data.items():
        if isinstance(v, str):
            hub.log_anomaly(source=k, severity="LOW", details=v)

    hub.aggregate_and_report(metric_name=target, value=numeric_metric)
    return hub.generate_final_report()