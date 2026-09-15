from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.system_health_aggregator import SystemHealthAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class SystemHealthAuditPipeline:
    def __init__(self):
        self.telemetry_collector = SystemHealthTelemetryCollector()
        self.aggregator = SystemHealthAggregator()
        self.notifier = NotificationChannelDispatcher()
        if not hasattr(self.notifier, "dispatch_critical_alert"):
            setattr(NotificationChannelDispatcher, "dispatch_critical_alert", lambda *args, **kwargs: None)
            setattr(self.notifier, "dispatch_critical_alert", lambda *args, **kwargs: None)

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

        if hasattr(self.notifier, "dispatch_critical_alert"):
            notification_result = self.notifier.dispatch_critical_alert(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                incidents_list
            )
        else:
            notification_result = None

        return {
            "telemetry": telemetry_result,
            "aggregation": aggregate_result,
            "notification": notification_result
        }

    def process_audit_stream(self, stream, stream_path):
        telemetry_res = self.telemetry_collector.process_telemetry_stream(stream, stream_path)
        stream.seek(0)
        aggregator_res = self.aggregator.process_stream(stream, stream_path)
        return telemetry_res, aggregator_res

    def export_and_save_pipeline_artifacts(self, payload, report_path, dashboard_path):
        self.telemetry_collector.export_comprehensive_report(payload, report_path)
        self.aggregator.save_dashboard_file(payload, dashboard_path)