import os
import json
from skills.anomaly_pipeline import AnomalyPipeline
from skills.digest_exporter import DigestExporter


class AuditPipelineExporterError(Exception):
    """Кастомное исключение для ошибок AuditPipelineExporter."""
    pass


class AuditPipelineExporter:
    """
    Класс для сквозного объединения конвейера аномалий (AnomalyPipeline)
    и экспортёра дайджестов (DigestExporter).
    """
    def __init__(self, repo_path=None, log_path=None, threshold=None, pipeline=None, exporter=None):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        if pipeline is not None:
            self.pipeline = pipeline
        else:
            self.pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)

        if exporter is not None:
            self.exporter = exporter
        else:
            self.exporter = DigestExporter()

    def run_audit_and_export_json(self, execution_id, raw_metrics, output_json_path):
        try:
            self.pipeline.run_end_to_end(execution_id, raw_metrics)
            return self.exporter.export_json_report(output_json_path)
        except Exception as e:
            raise AuditPipelineExporterError(str(e))

    def run_audit_and_export_html(self, execution_id, raw_metrics, output_html_path):
        try:
            self.pipeline.run_end_to_end(execution_id, raw_metrics)
            return self.exporter.export_html_report(output_html_path)
        except Exception as e:
            raise AuditPipelineExporterError(str(e))

    def export_pipeline_stream(self, stream_id, output_path):
        try:
            return self.exporter.export_stream_to_json(stream_id, output_path)
        except Exception as e:
            raise AuditPipelineExporterError(str(e))

    def generate_and_export_audit_report(self, raw_data, output_path):
        # Дополняем raw_data обязательными ключами для AnomalyFilter
        # ('source', 'severity', 'details', 'telemetry_snapshot'),
        # чтобы избежать KeyError при вызове pipeline.run().
        enriched_data = dict(raw_data)
        if "source" not in enriched_data:
            enriched_data["source"] = "audit_pipeline_exporter"
        if "severity" not in enriched_data:
            enriched_data["severity"] = "LOW"
        if "details" not in enriched_data:
            enriched_data["details"] = f"Audit report for {enriched_data.get('id', 'unknown')}"
        if "telemetry_snapshot" not in enriched_data:
            enriched_data["telemetry_snapshot"] = {
                enriched_data.get("metric", "value"): enriched_data.get("value", 0.0)
            }

        self.pipeline.run(enriched_data)

        if hasattr(self.exporter, "visualizer") and self.exporter.visualizer is not None:
            self.exporter.visualizer.digest = {
                "digest_id": raw_data.get("id", raw_data.get("execution_id", "")),
                "title": raw_data.get("metric", "Audit Report"),
                "severity": raw_data.get("severity", "LOW"),
                "metrics": {
                    raw_data.get("metric", "metric"): raw_data.get("value", 0.0)
                }
            }

        if hasattr(self.exporter, "export_json_report"):
            return self.exporter.export_json_report(output_path)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(raw_data, f)
            return output_path