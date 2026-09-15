from skills.incident_aggregator import IncidentAggregator
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator
from skills.recovery_report_exporter import RecoveryReportExporter
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.patch_scheduler import PatchScheduler

class SystemHealthAggregator:
    def __init__(self):
        self.incident_aggregator = IncidentAggregator()
        self.dashboard_generator = RecoveryDashboardGenerator()
        self.report_exporter = RecoveryReportExporter()
        self.notification_dispatcher = NotificationChannelDispatcher()
        self.patch_scheduler = PatchScheduler()

    def calculate_health_index(self, module_name: str) -> dict:
        self.incident_aggregator.process_and_aggregate(module_name, "", "", "")
        try:
            health_data = self.dashboard_generator.aggregate_system_health(module_name)
        except TypeError:
            health_data = self.dashboard_generator.aggregate_system_health()
        return health_data

    def process_incoming_stream(self, stream) -> dict:
        return self.dashboard_generator.parse_stream_data(stream)

    def generate_full_report(self, module_name: str, error_msg: str, incident_id: str, audit_data: dict):
        report_dict = self.report_exporter.generate_comprehensive_report(
            module_name,
            error_msg,
            self.incident_aggregator,
            incident_id,
            audit_data
        )
        return str(report_dict)

    def notify_stakeholders(self, channel: str, payload: dict) -> bool:
        if channel not in self.notification_dispatcher.channels:
            self.notification_dispatcher.register_channel(channel, {"url": f"https://httpbin.org/post"})
        return self.notification_dispatcher.dispatch(channel, payload)

    def execute_recovery_sequence(self, incident_id: str, patch_payload: dict, mock_arg) -> bool:
        res = self.patch_scheduler.coordinate_and_schedule(incident_id, patch_payload, mock_arg)
        if hasattr(res, "success"):
            return bool(res.success)
        return bool(res)