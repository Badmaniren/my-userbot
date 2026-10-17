from skills.anomaly_logger import AnomalyLogger
from skills.digest_exporter import DigestExporter, DigestExporterError


class MockVisualizer:
    def get_summary_metrics(self):
        return {}


class MockStabilityDigest:
    pass


class AnomalyReportAggregator:
    def __init__(self, log_path=None, anomaly_logger=None, digest_exporter=None):
        if anomaly_logger is not None:
            self.logger = anomaly_logger
        else:
            self.logger = AnomalyLogger(log_path=log_path)

        if digest_exporter is not None:
            self.exporter = digest_exporter
        else:
            stability = MockStabilityDigest()
            visualizer = MockVisualizer()
            if hasattr(self.logger, "get_structured_report"):
                visualizer.get_summary_metrics = lambda: self.logger.get_structured_report()
            self.exporter = DigestExporter(stability_digest=stability, anomaly_visualizer=visualizer)

        self._ensure_visualizer()

    def _ensure_visualizer(self):
        viz = getattr(self.exporter, 'visualizer', None) or getattr(self.exporter, 'anomaly_visualizer', None)
        if viz is None:
            visualizer = MockVisualizer()
            if hasattr(self.logger, "get_structured_report"):
                visualizer.get_summary_metrics = lambda: self.logger.get_structured_report()
            setattr(self.exporter, 'visualizer', visualizer)
            setattr(self.exporter, 'anomaly_visualizer', visualizer)

    def log_new_anomaly(self, source, severity, details, telemetry_snapshot=None):
        return self.logger.log_anomaly(
            source,
            severity,
            details,
            telemetry_snapshot
        )

    def generate_json_digest(self, output_path):
        self._ensure_visualizer()
        return self.exporter.export_json_report(output_path)

    def generate_html_digest(self, output_path):
        self._ensure_visualizer()
        return self.exporter.export_html_report(output_path)

    def get_summary(self):
        return self.logger.get_structured_report()

    def purge_logs(self):
        return self.logger.clear_logs()

    def generate_comprehensive_report(self):
        return self.logger.get_structured_report()

    def export_report(self, output_path):
        self._ensure_visualizer()
        return self.exporter.export_json_report(output_path)