from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_notification_bridge import IncidentNotificationBridge

class IncidentNotificationBroadcaster:
    def __init__(self, dispatcher=None, template_engine=None, webhook_broadcaster=None, storage_dir=None):
        self.dispatcher = dispatcher
        self.template_engine = template_engine
        self.webhook_broadcaster = webhook_broadcaster
        self.storage_dir = storage_dir

        self.evaluator = IncidentSeverityEvaluator()
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=self.webhook_broadcaster,
            storage_dir=self.storage_dir
        )

    def broadcast_incident(self, incident_data, channel, template):
        severity = self.evaluator.calculate_severity_score(incident_data)
        result = self.bridge.process_incident(incident_data, channel, template, severity)
        if isinstance(result, dict):
            result["severity"] = severity
            return result
        return {
            "status": "success" if result else "duplicate",
            "success": bool(result),
            "severity": severity,
            "incident_id": incident_data.get("incident_id") or incident_data.get("id")
        }

    def ingest_and_broadcast_stream(self, file_stream, channel):
        return self.bridge.ingest_stream(file_stream, channel)

    def dispatch_critical_broadcast(self, aggregated_incident):
        return self.bridge.dispatch_critical_incident(aggregated_incident)

    def process_and_broadcast(self, incident_data, channel, template):
        try:
            if hasattr(self.bridge, "process_and_broadcast"):
                return self.bridge.process_and_broadcast(incident_data, channel, template)

            severity = self.evaluator.calculate_severity_score(incident_data)
            return self.bridge.process_incident(incident_data, channel, template, severity)
        except Exception as e:
            return {"status": "error", "error_message": str(e)}