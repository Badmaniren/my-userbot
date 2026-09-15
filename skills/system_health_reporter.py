import io
import json
import os
from skills.system_health_aggregator import SystemHealthAggregator
from skills.recovery_report_exporter import RecoveryReportExporter


class SystemHealthReporter:
    def __init__(self):
        self._aggregator = SystemHealthAggregator()
        self._exporter = RecoveryReportExporter()

    def _collect_system_metrics(self, module_name):
        return {
            "module": module_name,
            "incident_id": "",
            "error": "",
            "severity": "LOW"
        }

    def generate_health_report(self, module_name, incident_data=None, audit_summary=None, metrics=None):
        result = self._aggregator.collect_and_aggregate(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            None,
            None,
            None
        )
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)

    def parse_stream_data(self, stream):
        if not isinstance(stream, io.IOBase):
            return None
        return self._aggregator.parse_reporter_stream(stream)

    def export_report_file(self, payload, file_path):
        return self._aggregator.save_dashboard_file(payload, file_path)

    def export_health_report(self, health_report, file_path):
        return self._aggregator.save_health_report(health_report, file_path)

    def aggregate_system_metrics(self, incidents_list, patches_list):
        return self._aggregator.aggregate_system_metrics(incidents_list, patches_list)