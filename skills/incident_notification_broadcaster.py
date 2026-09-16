import json
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_template_engine import NotificationTemplateEngine

class IncidentNotificationBroadcaster:
    def __init__(self, bridge=None, severity_evaluator=None, template_engine=None, evaluator=None, engine=None):
        self.bridge = bridge or IncidentNotificationBridge()
        self.severity_evaluator = severity_evaluator or evaluator or IncidentSeverityEvaluator()
        self.template_engine = template_engine or engine or NotificationTemplateEngine()

    def broadcast_confirmed_threat(self, incident_payload=None, template_name=None, incident_data=None, channel=None):
        payload = incident_payload if incident_payload is not None else incident_data
        if payload is None:
            payload = {}

        if channel is not None and "channel" not in payload:
            payload = dict(payload)
            payload["channel"] = channel

        severity = self.severity_evaluator.calculate_severity_score(payload)

        rendered_text = None
        if self.template_engine and template_name:
            rendered_text = self.template_engine.render_text(template_name, payload)

        return self.bridge.process_incident(payload, severity, rendered_text)

    def process_incoming_stream(self, file_stream, channel):
        return self.bridge.ingest_stream(file_stream, channel)

    def dispatch_escalated_threat(self, aggregated_incident):
        return self.bridge.dispatch_critical_incident(aggregated_incident)