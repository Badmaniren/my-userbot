from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster

class IncidentNotificationBroadcaster:
    def __init__(self, severity_evaluator=None, webhook_broadcaster=None):
        self.severity_evaluator = severity_evaluator if severity_evaluator is not None else IncidentSeverityEvaluator()
        self.webhook_broadcaster = webhook_broadcaster if webhook_broadcaster is not None else NotificationWebhookBroadcaster()

    def handle_and_broadcast(self, module_name, exception, traceback_str, incident_id, template_name=None, raw_data=None):
        severity = self.severity_evaluator.evaluate(module_name, exception, traceback_str, incident_id)
        severity_val = severity
        if isinstance(severity, dict):
            severity_val = severity.get("severity", "LOW")

        self.webhook_broadcaster.broadcast_incident(
            severity=severity_val,
            incident_id=incident_id,
            raw_data=raw_data,
            template_name=template_name
        )
        return severity

    def process_stream_chain(self, module_name, stream_data, assigned_severity):
        self.severity_evaluator.evaluate_stream(module_name, stream_data)
        self.webhook_broadcaster.process_stream_and_broadcast(stream_data, assigned_severity)

    def register_and_dispatch(self, channel_name, config, dispatch_name, payload):
        self.webhook_broadcaster.register_webhook_channel(channel_name, config)
        self.webhook_broadcaster.dispatch_to_webhook(dispatch_name, payload)

    def export_report(self, context, file_path):
        self.webhook_broadcaster.export_notification_report(context, file_path)

    def handle_stream_bytes(self, module_name, stream_io, severity):
        stream_data = stream_io.read()
        self.severity_evaluator.evaluate_stream(module_name, stream_data)
        self.webhook_broadcaster.process_stream_and_broadcast(stream_data, severity)

    def process_and_broadcast(self, incident_id, severity, raw_data, channel_name):
        severity_val = severity
        if isinstance(severity, dict):
            severity_val = severity.get("severity", "LOW")

        payload = {
            "incident_id": incident_id,
            "severity": severity_val,
            "raw_data": raw_data
        }
        return self.webhook_broadcaster.dispatch_to_webhook(channel_name, payload)