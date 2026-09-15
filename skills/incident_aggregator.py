from skills.patch_metric_collector import PatchMetricCollector
from skills.dependency_audit_reporter import DependencyAuditReporter


class IncidentAggregator:
    def __init__(self, metric_collector=None, audit_reporter=None):
        self.metric_collector = metric_collector if metric_collector is not None else PatchMetricCollector()
        self.audit_reporter = audit_reporter if audit_reporter is not None else DependencyAuditReporter()

    def aggregate_and_report(self, module_name, export_format):
        metrics_summary = self.metric_collector.get_metrics_summary(module_name)
        audit_report = self.audit_reporter.generate_report(module_name)

        payload = {
            'module_name': module_name,
            'metrics_summary': metrics_summary,
            'audit_report': audit_report
        }

        return self.audit_reporter.export_summary(payload, export_format)

    def record_incident_metric(self, payload):
        return self.metric_collector.record_metric(payload)

    def finalize_health_epic(self, epic_id, stream):
        return self.audit_reporter.finalize_epic(epic_id, stream)

    def export_system_health_metrics(self, path, format_type):
        return self.metric_collector.export_metrics(path, format_type)

    def generate_epic_report(self, payload, path):
        return self.audit_reporter.generate_epic_report(payload, path)

    def generate_health_report(self, module_name, audit_data, metrics_payload):
        metrics_summary = self.metric_collector.get_metrics_summary(module_name)
        audit_report = self.audit_reporter.generate_report(audit_data)

        incident_id = metrics_payload.get("incident_id", "") if isinstance(metrics_payload, dict) else ""

        return f"Health Report for {module_name}. Incident ID: {incident_id}. Metrics: {metrics_summary}. Audit: {audit_report}"