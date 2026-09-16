import os
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.incident_aggregator import IncidentAggregator

class IncidentAutoEscalationEngine:
    def __init__(self, incident_aggregator=None, severity_evaluator=None, trend_analyzer=None):
        self.incident_aggregator = incident_aggregator if incident_aggregator is not None else IncidentAggregator()
        self.severity_evaluator = severity_evaluator if severity_evaluator is not None else IncidentSeverityEvaluator()
        self.trend_analyzer = trend_analyzer if trend_analyzer is not None else IncidentTrendAnalyzer()

        # Обеспечиваем наличие хранилища инцидентов для интеграционных тестов, обращающихся напрямую к агрегатору
        if not hasattr(self.incident_aggregator, "incidents"):
            self.incident_aggregator.incidents = {}

    def process_escalation(self, incident_id):
        details = self.incident_aggregator.get_incident_details(incident_id)
        if not details:
            details = {}
        severity_score = details.get("severity_score")
        failure_history_count = details.get("failure_history_count")

        evaluated_score = self.severity_evaluator.evaluate(severity_score) if self.severity_evaluator else severity_score
        escalation_tier = self.trend_analyzer.determine_escalation_tier(failure_history_count) if self.trend_analyzer else None

        self.incident_aggregator.update_status(incident_id, "escalated", tier=escalation_tier)

        return {
            "incident_id": incident_id,
            "escalation_tier": escalation_tier,
            "severity_score": evaluated_score
        }

    def handle_stream_escalation(self, stream_payload):
        return self.incident_aggregator.ingest_raw_stream(stream_payload)

    def evaluate_and_escalate(self, incident_id):
        details = self.incident_aggregator.get_incident_details(incident_id)
        if not details:
            details = {"metric_value": 0.0, "storage_path": ""}

        metric_value = details.get("metric_value", 0.0)
        storage_path = details.get("storage_path", "")

        if storage_path:
            marker_file = os.path.join(storage_path, f"escalation_{incident_id}.lock")
            with open(marker_file, "w", encoding="utf-8") as f:
                f.write(f"Escalated with metric value: {metric_value}")

        return {
            "escalated": True,
            "target_incident_id": incident_id
        }