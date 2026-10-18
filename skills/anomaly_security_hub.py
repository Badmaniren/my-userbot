import os
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class AnomalySecurityHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        # Если log_path указывает на директорию, перенаправляем в файл внутри неё,
        # чтобы избежать IsADirectoryError при открытии логов на запись.
        if os.path.isdir(log_path):
            self.log_path = os.path.join(log_path, "anomaly_security.log")
        else:
            self.log_path = log_path

        self.threshold = threshold

        self.audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        self.logger = AnomalyLogger(log_path=self.log_path)

    def log_anomaly(self, source: str, severity: str, details, telemetry_snapshot: dict):
        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float):
        return self.audit_hub.aggregate_and_report(metric_name=metric_name, value=value)

    def generate_final_report(self) -> dict:
        audit_report = self.audit_hub.generate_final_report()
        logger_report = self.logger.get_structured_report()
        return {
            "audit_report": audit_report,
            "logger_report": logger_report
        }

    def get_structured_report(self):
        if hasattr(self.logger, 'get_structured_report'):
            return self.logger.get_structured_report()
        return self.audit_hub.generate_final_report()

    def get_anomalies(self) -> list:
        if hasattr(self.logger, 'get_anomalies'):
            return self.logger.get_anomalies()
        if hasattr(self.audit_hub, 'get_anomalies'):
            return self.audit_hub.get_anomalies()
        return []

    def clear_logs(self):
        if hasattr(self.logger, 'clear_logs'):
            self.logger.clear_logs()
        if hasattr(self.audit_hub, 'clear_logs'):
            self.audit_hub.clear_logs()