import json
from skills.system_health_reporter import SystemHealthReporter
from skills.incident_aggregator import IncidentAggregator

class SystemHealthAggregator:
    def __init__(self):
        self.reporter = SystemHealthReporter()
        self.aggregator = IncidentAggregator()

    def handle_stream_report(self, stream):
        return self.reporter.parse_stream_data(stream)

    def export_current_health(self, parsed_data, export_path):
        return self.reporter.export_health_report(parsed_data, export_path)

    def compile_metrics(self, incidents_list, patches_list):
        return self.reporter.aggregate_system_metrics(incidents_list, patches_list)

    def collect_and_aggregate_health(
        self,
        module_name,
        exception_msg,
        traceback_str,
        incident_id,
        audit_summary,
        metrics
    ):
        incident_result = self.aggregator.process_and_aggregate(
            module_name,
            Exception(exception_msg),
            traceback_str,
            incident_id
        )

        if isinstance(incident_result, dict):
            incident_result.setdefault("incident_id", incident_id)
            incident_result.setdefault("module_name", module_name)

        health_report = self.reporter.generate_health_report(
            module_name=module_name,
            incident_data=incident_result,
            audit_summary=audit_summary,
            metrics=metrics
        )

        if isinstance(health_report, str):
            try:
                health_report = json.loads(health_report)
            except (json.JSONDecodeError, TypeError):
                health_report = {}

        if isinstance(health_report, dict):
            health_report["metrics"] = metrics

        return {
            "incident_aggregation": incident_result,
            "health_report": health_report
        }

    def export_aggregated_health(self, report, export_path):
        return self.reporter.export_health_report(report, export_path)


def aggregate_system_health(
    module_name,
    exception,
    traceback_str,
    incident_id,
    audit_summary,
    metrics
):
    aggregator_obj = IncidentAggregator()
    reporter_obj = SystemHealthReporter()

    incident_summary = aggregator_obj.process_and_aggregate(
        module_name,
        exception,
        traceback_str,
        incident_id
    )

    health_report = reporter_obj.generate_health_report(
        module_name=module_name,
        incident_data=incident_summary,
        audit_summary=audit_summary,
        metrics=metrics
    )

    if isinstance(health_report, str):
        try:
            health_report = json.loads(health_report)
        except (json.JSONDecodeError, TypeError):
            health_report = {}

    if isinstance(health_report, dict):
        health_report["metrics"] = metrics

    return {
        "health_report": health_report,
        "incident_summary": incident_summary
    }