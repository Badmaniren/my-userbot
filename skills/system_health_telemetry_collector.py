import json
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter
from skills.telemetry_streamer import TelemetryStreamer


class SystemHealthTelemetryCollector:
    def __init__(self):
        self.aggregator = SystemHealthAggregator()
        self.reporter = SystemHealthReporter()
        self.streamer = TelemetryStreamer()

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
        self.reporter.generate_health_report(module_name)
        return agg_result

    def collect(self, stream_id=None, *args, **kwargs):
        if stream_id is not None:
            return {"stream_id": stream_id, "status": "collected", **kwargs}
        return {"status": "collected", **kwargs}

    def process_telemetry_stream(self, stream, path):
        stream_result = self.aggregator.process_stream(stream, path)
        self.reporter.parse_stream_data(stream)
        return stream_result

    def process_stream(self, stream, path):
        return self.process_telemetry_stream(stream, path)

    def process_stream_data(self, stream, path):
        return self.process_telemetry_stream(stream, path)

    def export_comprehensive_report(self, payload, path):
        export_status = self.aggregator.export_dashboard_file(payload, path)
        report_status = self.reporter.export_report_file(payload, path)
        if export_status is not None:
            return export_status
        return report_status if report_status is not None else True

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
        
        report_payload = {module_name: agg_result, "status": "OK"}

        self.reporter.export_report_file(report_payload, report_path)
        self.export_comprehensive_report(report_payload, dashboard_path)
        
        stream_payload = json.dumps(report_payload)

        if hasattr(self.streamer, "stream_data"):
            self.streamer.stream_data(stream_payload)
        elif hasattr(self.streamer, "stream"):
            self.streamer.stream(stream_payload)
        elif hasattr(self.streamer, "push_telemetry"):
            self.streamer.push_telemetry(report_payload)
        else:
            self.streamer.stream_data(stream_payload)
            
        return {module_name: agg_result}


def system_health_telemetry_collector(payload=None, **kwargs):
    collector = SystemHealthTelemetryCollector()
    if payload is not None and isinstance(payload, dict):
        if "module_name" in payload and "report_path" in payload:
            return collector.collect_and_process_telemetry(
                payload.get("module_name"),
                payload.get("incident_data", {}),
                payload.get("audit_summary", ""),
                payload.get("metrics", {}),
                payload.get("dashboard_format", "json"),
                payload.get("incidents_list", []),
                payload.get("patches_list", []),
                payload.get("report_path"),
                payload.get("dashboard_path", payload.get("report_path"))
            )
        return collector.collect_and_aggregate_telemetry(
            payload.get("module_name", "default_module"),
            payload.get("incident_data", {}),
            payload.get("audit_summary", ""),
            payload.get("metrics", {}),
            payload.get("dashboard_format", "json"),
            payload.get("incidents_list", []),
            payload.get("patches_list", [])
        )
    return collector


def collect_telemetry(*args, **kwargs):
    collector = SystemHealthTelemetryCollector()
    return collector.collect(*args, **kwargs)


def collect_telemetry_metrics(*args, **kwargs):
    collector = SystemHealthTelemetryCollector()
    return collector.collect(*args, **kwargs)


def collect(*args, **kwargs):
    collector = SystemHealthTelemetryCollector()
    return collector.collect(*args, **kwargs)


def stream_metrics(*args, **kwargs):
    collector = SystemHealthTelemetryCollector()
    return collector.streamer.stream_data(*args, **kwargs)