from skills.incident_aggregator import aggregate_incidents
from skills.system_health_aggregator import get_aggregated_health_data

def generate_incident_digest(incidents, output_file, metadata):
    """
    Функция-обертка для интеграционного теста,
    соответствующая сигнатуре в тестах.
    """
    try:
        with open(output_file, 'w') as f:
            f.write(f"Report for Request: {metadata.get('request_id')}\n")
            for incident in incidents:
                f.write(f"- {incident}\n")

        return {
            "status": "success",
            "request_id": metadata.get("request_id")
        }
    except Exception:
        return {"status": "error"}

class IncidentDigestGenerator:
    def __init__(self, system_health_aggregator, incident_aggregator,
                 notification_template_engine, notification_channel_dispatcher):
        self.health_aggregator = system_health_aggregator
        self.incident_aggregator = incident_aggregator
        self.template_engine = notification_template_engine
        self.channel_dispatcher = notification_channel_dispatcher

    def generate_digest(self, stakeholder_id, timeframe_hours):
        health_data = self.health_aggregator.get_aggregated_health(timeframe_hours)
        incidents = self.incident_aggregator.get_incidents(timeframe_hours)

        return {
            "stakeholder_id": stakeholder_id,
            "timeframe_hours": timeframe_hours,
            "health_summary": health_data,
            "incidents": incidents
        }

    def send_digest(self, stakeholder_email, digest_data):
        rendered = self.template_engine.render(digest_data)
        return self.channel_dispatcher.dispatch(stakeholder_email, rendered)