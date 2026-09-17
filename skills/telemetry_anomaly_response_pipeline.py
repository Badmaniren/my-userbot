from skills.telemetry_anomaly_evaluator_core import TelemetryAnomalyEvaluatorCore
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class PipelineExecutionException(Exception):
    """Исключение при выполнении пайплайна реагирования на телеметрические аномалии."""
    pass


class TelemetryAnomalyResponsePipeline:
    """Пайплайн для связывания оценки аномалий телеметрии и эскалации инцидентов."""

    def __init__(self):
        self.evaluator_core = TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = IncidentAutoEscalationEngine()

    def _normalize_payload(self, payload) -> dict:
        if isinstance(payload, dict):
            normalized = dict(payload)
        else:
            normalized = {"raw_stream": payload}

        if "stream_id" not in normalized:
            normalized["stream_id"] = str(normalized.get("stream_uuid") or normalized.get("metric_id") or normalized.get("incident_id") or "default_stream")
        if "metric" not in normalized:
            normalized["metric"] = str(normalized.get("metric_id") or "default_metric")
        if "value" not in normalized:
            val = None
            for key in ("anomaly_score", "telemetry_spike", "value"):
                if key in normalized:
                    val = normalized[key]
                    break
            normalized["value"] = float(val) if val is not None else 0.0
        if "threshold" not in normalized:
            normalized["threshold"] = float(normalized.get("threshold", 50.0))

        return normalized

    def process_telemetry_stream(self, telemetry_stream_bytes) -> dict:
        self.evaluator_core.evaluate_stream_source(telemetry_stream_bytes)
        self.escalation_engine.evaluate_system_telemetry_risks()
        payload = self._normalize_payload(telemetry_stream_bytes)
        evaluation_result = self.evaluator_core.evaluate_with_incident_trigger(payload)
        escalation_result = self.escalation_engine.process_escalation("default-incident")
        return {
            "evaluation": evaluation_result,
            "escalation": escalation_result
        }

    def evaluate_and_respond(self, payload: dict) -> dict:
        try:
            norm_payload = self._normalize_payload(payload)
            evaluation = self.evaluator_core.evaluate(norm_payload)
            patch_triggered = self.escalation_engine.check_and_trigger_patching()
            severity = evaluation.get("severity") if isinstance(evaluation, dict) else None
            return {
                "patch_triggered": patch_triggered,
                "severity": severity,
                "evaluation": evaluation
            }
        except Exception as e:
            if isinstance(e, PipelineExecutionException):
                raise
            raise PipelineExecutionException(str(e)) from e

    def handle_stream_escalation_cycle(self) -> dict:
        consumed_bytes = self.escalation_engine.consume_stream_data()
        evaluation_metrics = self.evaluator_core.evaluate_stream_source(consumed_bytes)
        return {
            "consumed_bytes": consumed_bytes,
            "evaluation_metrics": evaluation_metrics
        }


def run_telemetry_anomaly_response_pipeline(payload: dict) -> dict:
    pipeline = TelemetryAnomalyResponsePipeline()
    norm_payload = pipeline._normalize_payload(payload)
    eval_result = pipeline.evaluator_core.evaluate(norm_payload)
    escalation_result = pipeline.escalation_engine.process_escalation(
        payload.get("incident_id", "default-incident")
    )
    return {
        "evaluation_result": eval_result,
        "escalation_result": escalation_result
    }