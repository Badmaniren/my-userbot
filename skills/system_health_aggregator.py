from skills.incident_aggregator import IncidentAggregator
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator
from skills.recovery_report_exporter import RecoveryReportExporter
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class SystemHealthAggregator:
    """Модуль для агрегации метрик здоровья системы и формирования комплексных отчетов производительности и сбоев."""

    def __init__(self):
        self.IncidentAggregator = IncidentAggregator
        self.RecoveryDashboardGenerator = RecoveryDashboardGenerator
        self.RecoveryReportExporter = RecoveryReportExporter
        self.ErrorRecoveryHub = ErrorRecoveryHub
        self.NotificationChannelDispatcher = NotificationChannelDispatcher

    def aggregate_system_health(self):
        dashboard = RecoveryDashboardGenerator()
        return dashboard.aggregate_system_health()

    def process_stream(self, stream_io):
        dashboard = RecoveryDashboardGenerator()
        return dashboard.parse_stream_data(stream_io)

    def generate_report(self, *args, **kwargs):
        exporter = RecoveryReportExporter()
        if hasattr(exporter, "finalize_and_export_summary"):
            try:
                return exporter.finalize_and_export_summary(*args, **kwargs)
            except TypeError:
                pass
        return exporter.finalize_and_export_summary(args[0], args[-1] if args else kwargs.get("format_type"))

    def trigger_recovery(self, module, exception_type, incident_id):
        hub = ErrorRecoveryHub()
        return hub.analyze_and_recover(module, exception_type, incident_id)

    def notify_incident(self, severity, incident_id):
        dispatcher = NotificationChannelDispatcher()
        payload = {"incident_id": incident_id, "severity": severity}
        return dispatcher.dispatch(severity, payload)