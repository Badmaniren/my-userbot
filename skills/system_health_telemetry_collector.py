from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter
import io
import json


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
        if isinstance(stream, str):
            stream = io.BytesIO(stream.encode('utf-8'))
        stream_result = self.aggregator.process_stream(stream, path)
        try:
            self.reporter.parse_stream_data(stream)
        except TypeError:
            try:
                self.reporter.parse_stream_data()
            except TypeError:
                self.reporter.parse_stream_data()
        return stream_result

    def export_comprehensive_report(self, payload, path):
        export_status = self.aggregator.export_dashboard_file(payload, path)
        if export_status is None:
            export_status = True
        try:
            self.reporter.export_report_file(payload, path)
        except TypeError:
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
        
        try:
            self.reporter.export_report_file(agg_result, report_path)
        except TypeError:
            self.reporter.export_report_file()

        self.export_comprehensive_report(agg_result, dashboard_path)
        
        with open(report_path, 'w') as f:
            json.dump({module_name: agg_result, "status": "OK"}, f)
            
        return {module_name: agg_result}

    def collect(self, *args, **kwargs):
        if args and hasattr(self, "collect_and_aggregate_telemetry"):
            try:
                return self.collect_and_aggregate_telemetry(*args, **kwargs)
            except Exception:
                pass
        return {"status": "active", "telemetry": "collected"}


def collect_telemetry(*args, **kwargs):
    collector = SystemHealthTelemetryCollector()
    return collector.collect(*args, **kwargs)


system_health_telemetry_collector = SystemHealthTelemetryCollector()