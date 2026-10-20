import json
import os
from skills.digest_dashboard_builder import DigestDashboardBuilder, DigestDashboardBuilderError
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer


class DigestAuditPipeline:
    def __init__(self, digest_data, anomaly_visualizer=None, stability_digest=None):
        self.digest_data = digest_data
        self.anomaly_visualizer = anomaly_visualizer if anomaly_visualizer is not None else AnomalyVisualizer(digest_data)
        self.stability_digest = stability_digest if stability_digest is not None else digest_data
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )
        self.builder = DigestDashboardBuilder(
            digest_data=self.digest_data,
            anomaly_visualizer=self.anomaly_visualizer,
            digest_exporter=self.exporter
        )

    def run_export_json(self, output_path: str) -> str:
        if hasattr(self.exporter, 'export_json_report'):
            try:
                return self.exporter.export_json_report(output_path)
            except (TypeError, AttributeError):
                pass
        if hasattr(self.exporter, 'export_to_json'):
            try:
                return self.exporter.export_to_json(self.digest_data, output_path)
            except TypeError:
                return self.exporter.export_to_json(output_path)
        raise DigestExporterError("Exporter does not support JSON export methods.")

    def run_export_html(self, output_path: str) -> str:
        if hasattr(self.exporter, 'export_html_report'):
            try:
                return self.exporter.export_html_report(output_path)
            except (TypeError, AttributeError):
                pass
        if hasattr(self.exporter, 'export_to_html'):
            try:
                return self.exporter.export_to_html(self.digest_data, output_path)
            except TypeError:
                return self.exporter.export_to_html(output_path)
        raise DigestExporterError("Exporter does not support HTML export methods.")

    def build_audit_dashboard(self, json_path: str, html_path: str) -> str:
        return self.builder.build_dashboard(json_path, html_path)


def digest_audit_pipeline(digest_data, json_output_path: str, html_output_path: str, anomaly_visualizer=None, stability_digest=None):
    pipeline = DigestAuditPipeline(
        digest_data=digest_data,
        anomaly_visualizer=anomaly_visualizer,
        stability_digest=stability_digest
    )

    json_res = pipeline.run_export_json(json_output_path)
    html_res = pipeline.run_export_html(html_output_path)

    if not os.path.exists(json_output_path):
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(digest_data, f)

    if not os.path.exists(html_output_path):
        with open(html_output_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body>{json.dumps(digest_data)}</body></html>")

    dashboard_res = pipeline.build_audit_dashboard(json_res, html_res)
    return dashboard_res