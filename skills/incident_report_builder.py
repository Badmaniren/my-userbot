from skills.patch_metric_collector import PatchMetricCollector
from skills.dependency_audit_reporter import DependencyAuditReporter

class IncidentReportBuilder:
    def __init__(self):
        self.metric_collector = PatchMetricCollector()
        self.audit_reporter = DependencyAuditReporter()

    def build_report(self, random_metric_payload, random_audit_data):
        recorded = self.metric_collector.record_metric(random_metric_payload)
        report = self.audit_reporter.generate_report(random_audit_data)
        return f"{recorded} {report}"

    def export_analytics(self, random_epic_id, random_stream_data, random_format):
        self.audit_reporter.finalize_epic(random_epic_id, random_stream_data)
        return self.audit_reporter.export_summary(random_epic_id, random_stream_data, random_format)

    def generate_epic_incident_pipeline(self, module_name, random_payload, output_path):
        self.metric_collector.get_metrics_summary(module_name)
        return self.audit_reporter.generate_epic_report(module_name, random_payload, output_path)

    def export_raw_metrics(self, output_path, format_type):
        return self.metric_collector.export_metrics(output_path, format_type)

    def export_metrics(self, output_path, format_type):
        return self.metric_collector.export_metrics(output_path, format_type)

    def generate_summary_report(self, summary_payload):
        return str(summary_payload)

    def export_incident_report(self, summary_payload, export_path):
        with open(export_path, "w") as f:
            f.write(str(summary_payload))
        return True