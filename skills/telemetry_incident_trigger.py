from skills.telemetry_anomaly_evaluator_core import TelemetryAnomalyEvaluatorCore, AnomalyEvaluationException
from skills.incident_aggregator import IncidentAggregator


class TelemetryTriggerException(Exception):
    """Custom exception for telemetry trigger errors."""
    pass


class TelemetryIncidentTrigger:
    def __init__(self, module_name="telemetry_incident_trigger"):
        self.module_name = module_name
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.aggregator = IncidentAggregator()

    def process_telemetry(self, telemetry_payload: dict) -> dict:
        try:
            telemetry_payload.setdefault("stream_id", "default_stream")
            telemetry_payload.setdefault("metric", "default_metric")
            telemetry_payload.setdefault("value", 0.0)
            telemetry_payload.setdefault("threshold", 100.0)

            eval_result = self.evaluator.evaluate(telemetry_payload)
        except AnomalyEvaluationException as e:
            raise TelemetryTriggerException(str(e)) from e
        except Exception as e:
            raise TelemetryTriggerException(str(e)) from e

        anomaly_detected = eval_result.get("anomaly_detected", False) or eval_result.get("is_anomaly", False)
        incident_id = eval_result.get("incident_id") or telemetry_payload.get("incident_id")
        reason = eval_result.get("reason") or telemetry_payload.get("reason", "Anomaly detected")

        if anomaly_detected:
            self.aggregator.process_and_aggregate(
                self.module_name,
                Exception(reason),
                "Traceback dummy",
                incident_id
            )

            return {
                "success": True,
                "incident_triggered": True,
                "incident_id": incident_id
            }

        return {
            "success": True,
            "incident_triggered": False
        }

    def evaluate_stream(self, stream_source) -> dict:
        try:
            result = self.evaluator.evaluate_stream_source(stream_source)
            return {
                "success": True,
                "anomalies_found": result.get("anomalies_found", 0),
                "stream_processed": result.get("stream_processed", True)
            }
        except Exception as e:
            raise TelemetryTriggerException(str(e)) from e


def telemetry_incident_trigger_function_or_class(telemetry_payload: dict):
    trigger = TelemetryIncidentTrigger(module_name="telemetry_incident_trigger")
    return trigger.process_telemetry(telemetry_payload)
