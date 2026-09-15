from skills.system_health_reporter import SystemHealthReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator


class SystemHealthAggregator:
    def __init__(self):
        self.health_reporter = SystemHealthReporter()
        self.dashboard_generator = RecoveryDashboardGenerator()

    def aggregate_complex_health(self, module_name, incidents, patches):
        health_status = self.dashboard_generator.aggregate_system_health()
        metrics = self.health_reporter.aggregate_system_metrics(incidents, patches)

        incident_data = incidents[0] if incidents else {}
        if isinstance(incident_data, dict):
            incident_data = {**incident_data, "module_name": module_name}

        report = self.health_reporter.generate_health_report(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary={},
            metrics=metrics
        )
        return {
            "metrics": metrics,
            "health": health_status,
            "report": report
        }

    def process_stream_and_export(self, stream_mock, incidents, reports, format_type, path):
        stream_content = stream_mock.read()
        metrics = self.dashboard_generator.parse_stream_data(stream_content)
        dashboard = self.dashboard_generator.generate_dashboard(
            metrics, incidents, reports, format_type
        )
        export_result = self.dashboard_generator.export_dashboard_file(dashboard, path)
        return export_result

    def aggregate_comprehensive_health(self):
        return self.dashboard_generator.aggregate_system_health()