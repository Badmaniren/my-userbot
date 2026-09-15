from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter


class SystemHealthTelemetryCollector:
    def __init__(self):
        self.aggregator = SystemHealthAggregator()
        self.reporter = SystemHealthReporter()

    def collect_and_aggregate_telemetry(
        self,
        module_name,
        incident_data,
        audit_summary,
        metrics,
        dashboard_format,
        incidents_list,
        patches_list
    ):
        agg_result = self.aggregator.collect_and_aggregate(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list
        )
        try:
            self.reporter.generate_health_report(module_name)
        except TypeError:
            self.reporter.generate_health_report()
        return agg_result

    def process_telemetry_stream(self, stream, path):
        stream_result = self.aggregator.process_stream(stream, path)
        self.reporter.parse_stream_data()
        return stream_result

    def export_comprehensive_report(self, payload, path):
        export_status = self.aggregator.export_dashboard_file(payload, path)
        self.reporter.export_report_file()
        return export_status

    def collect_and_process_telemetry(
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
        agg_result = self.collect_and_aggregate_telemetry(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list
        )
        
        self.reporter.export_report_file()
        self.export_comprehensive_report(agg_result, dashboard_path)
        
        import json
        with open(report_path, 'w') as f:
            json.dump({module_name: agg_result, "status": "OK"}, f)
            
        return {module_name: agg_result}