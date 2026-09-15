from skills.system_health_audit_pipeline import SystemHealthAuditPipeline
from skills.system_health_reporter import SystemHealthReporter


class SystemHealthMonitoringGateway:
    def __init__(self):
        self.audit_pipeline = SystemHealthAuditPipeline()
        self.reporter = SystemHealthReporter()

    def run_monitoring_gateway_pipeline(
        self,
        module_name,
        incident_data,
        audit_summary,
        metrics,
        dashboard_format,
        incidents_list,
        patches_list,
        report_path,
        dashboard_path
    ):
        return self.audit_pipeline.run_audit_pipeline(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list,
            report_path,
            dashboard_path
        )

    def process_monitoring_gateway_stream(self, stream, stream_path):
        return self.audit_pipeline.process_audit_stream(stream, stream_path)

    def export_monitoring_gateway_artifacts(self, payload, report_path, dashboard_path):
        return self.audit_pipeline.export_and_save_pipeline_artifacts(
            payload, report_path, dashboard_path
        )

    def generate_gateway_health_report(
        self, module_name, incident_data, audit_summary, metrics
    ):
        return self.reporter.generate_health_report(
            module_name, incident_data, audit_summary, metrics
        )

    def parse_gateway_stream_data(self, stream):
        return self.reporter.parse_stream_data(stream)

    def export_gateway_report_file(self, payload, file_path):
        return self.reporter.export_report_file(payload, file_path)

    def export_gateway_health_report(self, health_report, file_path):
        return self.reporter.export_health_report(health_report, file_path)

    def aggregate_gateway_system_metrics(self, incidents_list, patches_list):
        return self.reporter.aggregate_system_metrics(incidents_list, patches_list)

    def execute_monitoring_and_reporting_pipeline(
        self,
        module_name,
        incident_data,
        audit_summary,
        metrics,
        dashboard_format,
        incidents_list,
        patches_list,
        report_path,
        dashboard_path
    ):
        audit_result = self.run_monitoring_gateway_pipeline(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list,
            report_path,
            dashboard_path
        )

        health_report = self.generate_gateway_health_report(
            module_name, incident_data, audit_summary, metrics
        )

        if isinstance(health_report, str):
            health_report = {
                "module_name": module_name,
                "incident_data": incident_data,
                "audit_summary": audit_summary,
                "metrics": metrics,
                "report": health_report
            }
        elif isinstance(health_report, dict) and "module_name" not in health_report:
            health_report["module_name"] = module_name
            if "audit_summary" not in health_report:
                health_report["audit_summary"] = audit_summary

        self.export_gateway_report_file(health_report, report_path)

        return {
            "audit_pipeline_result": audit_result,
            "health_report": health_report
        }

    def export(self, audited_data, **kwargs):
        summary = {
            "status": "EXPORTED",
            "audited_summary": audited_data,
            "system_health": "OPTIMAL"
        }
        return summary