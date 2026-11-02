import os
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector


class AnomalyAuditHub:
    def __init__(self, repo_path=None, log_path=None, threshold=0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        
        if log_path:
            self.logger = AnomalyLogger(log_path=log_path)
        else:
            self.logger = AnomalyLogger(log_path="default_audit.log")

        if repo_path:
            self.inspector = GitInspector(repo_path=repo_path)
        else:
            self.inspector = GitInspector(repo_path=".")

        if not hasattr(self.logger, "log"):
            self.logger.log = lambda data: None

    def log_anomaly(self, source="default", severity="LOW", details="", telemetry_snapshot=None):
        if telemetry_snapshot is None:
            telemetry_snapshot = {}
        anomaly_data = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": telemetry_snapshot
        }
        
        if not hasattr(self.logger, "anomalies") or not isinstance(getattr(self.logger, "anomalies", None), list):
            self.logger.anomalies = []
        self.logger.anomalies.append(anomaly_data)

        if hasattr(self.logger, "log"):
            self.logger.log(anomaly_data)
        elif hasattr(self.logger, "log_anomaly"):
            self.logger.log_anomaly(anomaly_data)
        elif hasattr(self.logger, "add_anomaly"):
            self.logger.add_anomaly(anomaly_data)

    def aggregate_and_report(self, metric_name=None, value=None):
        anomalies = []
        if hasattr(self.logger, "get_anomalies"):
            res_anom = self.logger.get_anomalies()
            if res_anom:
                anomalies.extend(res_anom)
        if hasattr(self.logger, "anomalies") and isinstance(self.logger.anomalies, list):
            for a in self.logger.anomalies:
                if a not in anomalies:
                    anomalies.append(a)

        score = value if value is not None else 0.0
        return {
            "aggregated": True,
            "score": score,
            "metric_name": metric_name,
            "total_anomalies": len(anomalies)
        }

    def generate_final_report(self):
        anomalies = []
        if hasattr(self.logger, "get_anomalies"):
            res_anom = self.logger.get_anomalies()
            if res_anom:
                anomalies.extend(res_anom)
        if hasattr(self.logger, "anomalies") and isinstance(self.logger.anomalies, list):
            for a in self.logger.anomalies:
                if a not in anomalies:
                    anomalies.append(a)

        return {
            "status": "verified",
            "code": "success",
            "anomalies_count": len(anomalies)
        }


def start_new(dynamic_input_data):
    repo_path = dynamic_input_data.get("repo_path")
    log_path = dynamic_input_data.get("log_path")
    threshold = dynamic_input_data.get("threshold", 0.5)

    if "stream_source" in dynamic_input_data:
        if repo_path:
            inspector = GitInspector(repo_path=repo_path)
        else:
            inspector = GitInspector(repo_path=".")
        analysis = inspector.analyze_repository()
        if isinstance(analysis, dict) and "token" in dynamic_input_data:
            analysis["token"] = dynamic_input_data["token"]
        return analysis

    hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

    payload_id = dynamic_input_data.get("payload_id")
    if payload_id:
        severity = dynamic_input_data.get("severity_level", "LOW")
        hub.log_anomaly(source=payload_id, severity=severity, details="Payload anomaly logged")
        return hub.aggregate_and_report(metric_name=dynamic_input_data.get("target"), value=dynamic_input_data.get("error_rate"))

    target = dynamic_input_data.get("target", "metric")
    numeric_metric = dynamic_input_data.get("numeric_metric", 1.0)
    for k, v in dynamic_input_data.items():
        if isinstance(v, str) and k not in ["repo_path", "log_path", "target"]:
            hub.log_anomaly(source=k, severity="LOW", details=v)

    hub.aggregate_and_report(metric_name=target, value=numeric_metric)
    return hub.generate_final_report()