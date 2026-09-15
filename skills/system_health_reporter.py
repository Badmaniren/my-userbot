import io
import json
import os
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator


class SystemHealthReporter:
    def __init__(self):
        pass

    def _collect_system_metrics(self, module_name):
        return {
            "module": module_name,
            "incident_id": "",
            "error": "",
            "severity": "LOW"
        }

    def generate_health_report(self, module_name, incident_data=None, audit_summary=None, metrics=None):
        metrics_data = self._collect_system_metrics(module_name)
        
        if isinstance(incident_data, dict):
            metrics_data.update(incident_data)
            if "incident_id" in incident_data:
                metrics_data["incident_id"] = incident_data["incident_id"]
        
        report_dict = {
            "module": module_name,
            "metrics": metrics_data,
            "incident_data": incident_data,
            "audit_summary": audit_summary,
            "system_metrics": metrics
        }
        
        return json.dumps(report_dict, ensure_ascii=False)

    def parse_stream_data(self, stream):
        if not isinstance(stream, io.IOBase):
            return None
        
        raw_bytes = stream.read()
        return {
            "raw_length": len(raw_bytes),
            "data": raw_bytes
        }

    def export_report_file(self, payload, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(payload, dict):
                    json.dump(payload, f, ensure_ascii=False)
                else:
                    f.write(str(payload))
            return True
        except Exception:
            return False

    def export_health_report(self, health_report, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(health_report, (dict, list)):
                    json.dump(health_report, f, ensure_ascii=False)
                else:
                    f.write(str(health_report))
            return True
        except Exception:
            return False

    def aggregate_system_metrics(self, incidents_list, patches_list):
        return {
            "total_incidents": len(incidents_list) if incidents_list else 0,
            "total_patches": len(patches_list) if patches_list else 0
        }


def system_health_reporter(diagnostic_result=None, output_path=None, *args, **kwargs):
    reporter = SystemHealthReporter()
    if output_path is not None:
        return reporter.export_report_file(diagnostic_result, output_path)
    if diagnostic_result is not None:
        return True
    return reporter