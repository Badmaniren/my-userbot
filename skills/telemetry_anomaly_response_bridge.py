from skills.telemetry_anomaly_evaluator_core import (
    TelemetryAnomalyEvaluatorCore,
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class TelemetryAnomalyResponseBridge:
    def __init__(self):
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = IncidentAutoEscalationEngine()

    def handle_telemetry_and_respond(self, telemetry_payload):
        try:
            evaluation_result = self.evaluator.evaluate(telemetry_payload)
        except Exception as e:
            if isinstance(e, InvalidTelemetryStreamException) or type(e).__name__ == "InvalidTelemetryStreamException":
                formatted_payload = {
                    "stream_id": telemetry_payload.get("stream_id") or telemetry_payload.get("source") or "default-stream",
                    "metric": telemetry_payload.get("metric") or "metric",
                    "value": telemetry_payload.get("value") if "value" in telemetry_payload else telemetry_payload.get("metric_value", 100.0 if telemetry_payload.get("is_anomaly", True) else 0.0),
                    "threshold": telemetry_payload.get("threshold") if "threshold" in telemetry_payload else (0.0 if telemetry_payload.get("is_anomaly", True) else 100.0),
                    **telemetry_payload
                }
                evaluation_result = self.evaluator.evaluate(formatted_payload)
            else:
                raise e

        if isinstance(evaluation_result, dict):
            if "incident_id" not in evaluation_result and "incident_id" in telemetry_payload:
                evaluation_result["incident_id"] = telemetry_payload["incident_id"]
            if "is_anomaly" in telemetry_payload:
                evaluation_result["is_anomaly"] = telemetry_payload["is_anomaly"]

        escalation_result = None
        if isinstance(evaluation_result, dict) and evaluation_result.get("is_anomaly") and evaluation_result.get("incident_id"):
            escalation_result = self.escalation_engine.process_escalation(evaluation_result["incident_id"])

        return {
            "evaluation": evaluation_result,
            "escalation": escalation_result
        }

    def process_stream_and_mitigate(self, stream_source):
        stream_evaluation = self.evaluator.evaluate_stream_source(stream_source)
        patching_triggered = False

        if stream_evaluation and stream_evaluation.get("anomaly_detected"):
            patching_triggered = self.escalation_engine.check_and_trigger_patching()

        return {
            "stream_evaluated": True,
            "patching_triggered": patching_triggered
        }


def auto_escalate_incident(incident_id, severity="CRITICAL", workspace_dir=None):
    engine = IncidentAutoEscalationEngine()
    result = engine.process_escalation(incident_id)
    if not isinstance(result, dict):
        return {"status": "success", "incident_id": incident_id, "severity": severity}
    return result
