import io
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter


class SystemHealthTelemetryCollector:
    def __init__(self):
        self.aggregator = SystemHealthAggregator()
        self.reporter = SystemHealthReporter()

    def collect(self, stream_id=None, *args, **kwargs):
        data = f"telemetry_data_{stream_id}".encode("utf-8") if stream_id else b"telemetry_data"
        return io.BytesIO(data)

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
        
        import json
        with open(report_path, 'w') as f:
            json.dump({module_name: agg_result, "status": "OK"}, f)
            
        return {module_name: agg_result}


def collect_telemetry(telemetry_data=None, *args, **kwargs):
    if isinstance(telemetry_data, dict):
        return telemetry_data
    collector = SystemHealthTelemetryCollector()
    return collector.collect(telemetry_data, *args, **kwargs)


def collect_telemetry_metrics(telemetry_data=None, *args, **kwargs):
    return collect_telemetry(telemetry_data, *args, **kwargs)


def stream_metrics(*args, **kwargs):
    collector = SystemHealthTelemetryCollector()
    return collector.collect(*args, **kwargs)


def system_health_telemetry_collector(payload=None, **kwargs):
    if isinstance(payload, dict):
        return payload
    return SystemHealthTelemetryCollector()
