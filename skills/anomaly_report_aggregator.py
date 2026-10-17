from skills.anomaly_logger import AnomalyLogger
from skills.digest_exporter import DigestExporter, DigestExporterError


class AnomalyReportAggregator:
    def __init__(self, log_path=None, anomaly_logger=None, digest_exporter=None):
        if anomaly_logger is not None:
            self.logger = anomaly_logger
        else:
            self.logger = AnomalyLogger(log_path=log_path)

        if digest_exporter is not None:
            self.exporter = digest_exporter
        else:
            self.exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)

    def log_new_anomaly(self, source, severity, details, telemetry_snapshot=None):
        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def generate_json_digest(self, output_path):
        return self.exporter.export_json_report(output_path)

    def generate_html_digest(self, output_path):
        return self.exporter.export_html_report(output_path)

    def get_summary(self):
        return self.logger.get_structured_report()

    def purge_logs(self):
        return self.logger.clear_logs()

    def generate_comprehensive_report(self):
        return self.logger.get_structured_report()

    def export_report(self, output_path):
        return self.exporter.export_json_report(output_path)