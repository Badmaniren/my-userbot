from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.system_health_aggregator import SystemHealthAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class SystemHealthAuditPipeline:
    def __init__(self, monitoring_gateway=None):
        from skills.system_health_monitoring_gateway import SystemHealthMonitoringGateway
        self.telemetry_collector = SystemHealthTelemetryCollector()
        self.aggregator = SystemHealthAggregator()
        self.monitoring_gateway = monitoring_gateway if monitoring_gateway is not None else SystemHealthMonitoringGateway(audit_pipeline=self)
        self.notification_dispatcher = NotificationChannelDispatcher()

    def run_audit_pipeline(
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
        if not hasattr(self.monitoring_gateway, "capture_system_state"):
            self.monitoring_gateway.capture_system_state = lambda module_name, metrics, incident_data: {
                "module_name": module_name,
                "metrics": metrics,
                "incident_data": incident_data
            }

        telemetry_result = self.telemetry_collector.collect_and_process_telemetry(
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
        
        aggregate_result = self.aggregator.collect_and_aggregate(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list
        )

        return {
            "telemetry": telemetry_result,
            "aggregation": aggregate_result
        }

    def process_audit_stream(self, stream, stream_path):
        if hasattr(self.telemetry_collector, "reporter") and self.telemetry_collector.reporter:
            if hasattr(self.telemetry_collector.reporter, "parse_stream_data"):
                import inspect
                sig = inspect.signature(self.telemetry_collector.reporter.parse_stream_data)
                if len(sig.parameters) > 0:
                    self.telemetry_collector.reporter.parse_stream_data(stream)

        telemetry_res = self.telemetry_collector.process_telemetry_stream(stream, stream_path)
        stream.seek(0)
        aggregator_res = self.aggregator.process_stream(stream, stream_path)
        return telemetry_res, aggregator_res

    def export_and_save_pipeline_artifacts(self, payload, report_path, dashboard_path):
        self.telemetry_collector.export_comprehensive_report(payload, report_path)
        self.aggregator.save_dashboard_file(payload, dashboard_path)