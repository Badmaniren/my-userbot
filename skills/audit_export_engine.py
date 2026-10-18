import json
import os
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class AuditExportEngine:
    def __init__(self, repo_path=None, log_path=None, threshold=None, audit_hub=None, logger=None):
        if audit_hub is not None:
            self.audit_hub = audit_hub
        else:
            self.audit_hub = AnomalyAuditHub(
                repo_path=repo_path, log_path=log_path, threshold=threshold
            )

        if logger is not None:
            self.logger = logger
        else:
            self.logger = AnomalyLogger(log_path=log_path)

    def log_and_export_anomaly(self, source, severity, details, telemetry_snapshot):
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
        report = self.audit_hub.generate_final_report()
        if isinstance(report, list):
            return {
                "status": "ok",
                "anomalies": report,
                "total_count": len(report)
            }
        return report

    def aggregate_metric_and_export(self, metric_name, value):
        return self.audit_hub.aggregate_and_report(metric_name=metric_name, value=value)

    def export_structured_logs(self):
        return self.logger.get_structured_report()

    def clear_audit_history(self):
        self.logger.clear_logs()

    def stream_export_data(self):
        return self.logger.get_anomalies()

    def export_audit_report(self, export_path):
        anomalies = self.logger.get_anomalies()
        serialized_anomalies = []
        for a in anomalies:
            if isinstance(a, dict):
                serialized_anomalies.append(a)
            else:
                serialized_anomalies.append({"raw_data": str(a)})

        report_data = {
            "structured_logs": serialized_anomalies,
            "final_report": self.audit_hub.generate_final_report()
        }
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)
        return export_path