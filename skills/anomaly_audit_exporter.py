import json
from typing import Any, Dict, Optional

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class AnomalyAuditExporterError(Exception):
    """Кастомное исключение для ошибок экспортера аудита аномалий."""
    pass


class AnomalyAuditExporter:
    """Связывает AnomalyAuditHub и AnomalyLogger для безопасного экспорта отчетов."""

    def __init__(self, repo_path: str, log_path: str, threshold: float) -> None:
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.hub = AnomalyAuditHub(repo_path, log_path, threshold)
        self.logger = AnomalyLogger(log_path)

    def log_anomaly(
        self,
        source: str,
        severity: str,
        details: Dict[str, Any],
        telemetry_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            self.hub.log_anomaly(source, severity, details, telemetry_snapshot)
            self.logger.log_anomaly(source, severity, details, telemetry_snapshot)
        except Exception as exc:
            raise AnomalyAuditExporterError(str(exc)) from exc

    def aggregate_and_report(self, metric_name: str, metric_value: float) -> Dict[str, Any]:
        try:
            res = self.hub.aggregate_and_report(metric_name, metric_value)
            if isinstance(res, list):
                return {
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "report": res,
                    "total_anomalies": len(res),
                }
            if isinstance(res, dict):
                return res
            return {"metric_name": metric_name, "metric_value": metric_value, "report": res}
        except Exception as exc:
            raise AnomalyAuditExporterError(str(exc)) from exc

    def export_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        try:
            hub_report = self.hub.generate_final_report()
            logger_report = self.logger.get_structured_report()
            report = {
                "hub_report": hub_report,
                "logger_report": logger_report,
            }

            if output_path is not None:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

            return report
        except Exception as exc:
            raise AnomalyAuditExporterError(str(exc)) from exc