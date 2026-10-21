from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.system_telemetry import SystemTelemetry


class AuditExportPipeline:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.audit_hub = AnomalyAuditHub(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold
        )
        self.telemetry = SystemTelemetry(repo_path=repo_path)
        self.stability_digest = StabilityDigest(
            repo_path=repo_path,
            anomaly_detector=self.audit_hub.aggregator.correlator,
            system_telemetry=self.telemetry
        )
        self.visualizer = AnomalyVisualizer()
        self.digest_exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.visualizer
        )

    def run_audit_and_export(
        self,
        source: str,
        severity: str,
        details: str,
        telemetry_snapshot: dict,
        metric_name: str,
        metric_value: float,
        output_json_path: str
    ):
        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.audit_hub.generate_final_report()
        self.digest_exporter.export_json_report(output_json_path)

    def export_stream(self, stream_id: str, output_path: str) -> str:
        return self.digest_exporter.export_stream_to_json(stream_id, output_path)