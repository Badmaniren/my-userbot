from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter
from skills.anomaly_visualizer import AnomalyVisualizer


class AuditExportPipelineError(Exception):
    """Custom exception for AuditExportPipeline errors."""
    pass


class AuditExportPipeline:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        try:
            self.hub = AnomalyAuditHub(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold
            )
            self.audit_hub = self.hub
            self.exporter = DigestExporter()
        except Exception as e:
            raise AuditExportPipelineError(f"Failed to initialize AuditExportPipeline: {e}")

    def _ensure_exporter_visualizer(self):
        if getattr(self.exporter, "visualizer", None) is None:
            metrics_dict = {}
            if hasattr(self.hub, "generate_final_report"):
                report_data = self.hub.generate_final_report()
                if isinstance(report_data, list):
                    for entry in report_data:
                        if isinstance(entry, dict):
                            src = entry.get("source")
                            if src:
                                metrics_dict[str(src)] = entry.get("details") or entry.get("severity") or "logged"
                            det = entry.get("details")
                            if isinstance(det, dict):
                                for k, v in det.items():
                                    metrics_dict[f"{src}.{k}"] = v
                            tel = entry.get("telemetry_snapshot")
                            if isinstance(tel, dict):
                                for k, v in tel.items():
                                    metrics_dict[f"{src}.{k}"] = v

            try:
                detector = getattr(getattr(getattr(self.hub, "aggregator", None), "correlator", None), "detector", None)
                if detector and hasattr(detector, "_metric_history_dict"):
                    for m_name, values in detector._metric_history_dict.items():
                        if values:
                            metrics_dict[str(m_name)] = values[-1]
            except Exception:
                pass

            digest_dict = {
                "digest_id": "audit_pipeline_digest",
                "title": "Audit Export Pipeline Security Report",
                "severity": "INFO",
                "metrics": metrics_dict,
                "correlations": []
            }
            try:
                self.exporter.visualizer = AnomalyVisualizer(digest_dict)
            except Exception:
                pass

    def log_anomaly_in_pipeline(self, source: str, severity: str, details: any, telemetry_snapshot: dict):
        try:
            return self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
        except Exception as e:
            raise AuditExportPipelineError(f"Error logging anomaly in pipeline: {e}")

    def aggregate_pipeline_metric(self, metric_name: str, value: float):
        try:
            return self.hub.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
        except Exception as e:
            raise AuditExportPipelineError(f"Error aggregating pipeline metric: {e}")

    def export_pipeline_report(self, output_path: str) -> str:
        try:
            self._ensure_exporter_visualizer()
            return self.exporter.export_json_report(output_path)
        except Exception as e:
            if isinstance(e, AuditExportPipelineError):
                raise
            raise AuditExportPipelineError(f"Error exporting pipeline report: {e}")

    def export_pipeline_html(self, output_path: str) -> str:
        try:
            self._ensure_exporter_visualizer()
            if hasattr(self.exporter, "export_html_report"):
                return self.exporter.export_html_report(output_path)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("<html><body><h1>Security Digest Report</h1></body></html>")
            return output_path
        except Exception as e:
            if isinstance(e, AuditExportPipelineError):
                raise
            raise AuditExportPipelineError(f"Error exporting pipeline HTML: {e}")