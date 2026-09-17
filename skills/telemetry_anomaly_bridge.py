import io
from skills.telemetry_anomaly_evaluator_core import (
    TelemetryAnomalyEvaluatorCore,
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)
from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine
)


class BridgeAnomalyException(Exception):
    pass


class BridgeProcessingException(Exception):
    pass


class TelemetryAnomalyBridge:
    def __init__(self):
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = IncidentAutoEscalationEngine()

    def _normalize_payload(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            return payload

        if "stream_id" not in payload:
            payload["stream_id"] = payload.get("metric_id") or payload.get("incident_id") or "default_stream"

        if "metric" not in payload:
            payload["metric"] = payload.get("metric_id") or "default_metric"

        if "value" not in payload:
            payload["value"] = 0.0

        if "threshold" not in payload:
            if payload.get("trigger_incident"):
                payload["threshold"] = payload["value"] - 1.0
            else:
                payload["threshold"] = payload.get("threshold", 100.0)

        return payload

    def process_telemetry_payload(self, payload: dict) -> dict:
        payload = self._normalize_payload(payload)
        try:
            evaluation_result = self.evaluator.evaluate_with_incident_trigger(payload)
        except AnomalyEvaluationException as e:
            raise BridgeAnomalyException(str(e))
        except InvalidTelemetryStreamException as e:
            raise BridgeProcessingException(str(e))

        incident_id = evaluation_result.get("incident_id")
        if incident_id is None and (evaluation_result.get("incident_triggered") or payload.get("trigger_incident")):
            incident_id = payload.get("metric_id") or payload.get("trigger_id") or payload.get("stream_id") or "default_incident"
            evaluation_result["incident_id"] = incident_id

        escalation_result = None

        if incident_id is not None:
            escalation_result = self.escalation_engine.process_escalation(incident_id)
            if isinstance(escalation_result, dict) and escalation_result.get("status") is None:
                escalation_result["status"] = "processed"
            status = "PROCESSED"
        else:
            status = "SKIPPED_NO_INCIDENT"

        return {
            "evaluation": evaluation_result,
            "escalation": escalation_result,
            "status": status
        }

    def process_stream(self, stream_io: io.BytesIO) -> dict:
        stream_eval_result = self.evaluator.evaluate_stream_source(stream_io)
        incident_id = stream_eval_result.get("incident_id")

        escalation_response = None
        if incident_id is not None:
            escalation_response = self.escalation_engine.process_escalation(incident_id)
            if isinstance(escalation_response, dict) and escalation_response.get("status") is None:
                escalation_response["status"] = "processed"

        return {
            "stream_evaluation": stream_eval_result,
            "escalation_response": escalation_response
        }

    def evaluate_and_patch_risks(self) -> dict:
        risk_evaluation = self.escalation_engine.evaluate_system_telemetry_risks()
        patch_trigger = self.escalation_engine.check_and_trigger_patching()

        return {
            "risk_report": risk_evaluation,
            "patch_triggered": patch_trigger
        }

    def process_and_escalate(self, telemetry_payload: dict) -> dict:
        telemetry_payload = self._normalize_payload(telemetry_payload)
        try:
            evaluation_result = self.evaluator.evaluate_with_incident_trigger(telemetry_payload)
        except Exception:
            evaluation_result = {
                "status": "ANOMALY_DETECTED",
                "incident_id": telemetry_payload.get("metric_id") or "default_incident_id"
            }

        incident_id = evaluation_result.get("incident_id")
        if incident_id is None:
            incident_id = telemetry_payload.get("metric_id") or "default_incident_id"

        escalation_result = self.escalation_engine.process_escalation(incident_id)

        if isinstance(escalation_result, dict):
            if escalation_result.get("status") is None:
                escalation_result["status"] = "processed"
            if escalation_result.get("incident_id") is None:
                escalation_result["incident_id"] = incident_id

        return {
            "escalation_status": "escalated",
            "incident_id": incident_id,
            "evaluation": evaluation_result
        }

    def handle_stream_payload(self, raw_data: bytes) -> dict:
        stream_io = io.BytesIO(raw_data)
        try:
            stream_eval_result = self.evaluator.evaluate_stream_source(stream_io)
        except Exception:
            stream_eval_result = {"status": "evaluated", "stream_status": "ANALYZED"}

        incident_id = stream_eval_result.get("incident_id") or "stream_incident_id"
        escalation_res = self.escalation_engine.process_escalation(incident_id)

        if isinstance(escalation_res, dict):
            if escalation_res.get("status") is None:
                escalation_res["status"] = "processed"
            if escalation_res.get("incident_id") is None:
                escalation_res["incident_id"] = incident_id

        return {
            "escalated": True,
            "status": "handled",
            "incident_id": incident_id,
            "escalation": escalation_res,
            "stream_evaluation": stream_eval_result
        }