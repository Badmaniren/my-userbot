from skills.telemetry_anomaly_evaluator_core import (
    TelemetryAnomalyEvaluatorCore,
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class ConnectorException(Exception):
    """Кастомное исключение для ошибок коннектора телеметрии и эскалации."""
    pass


class TelemetryAnomalyResponseConnector:
    def __init__(self, workspace_dir=None, evaluator=None, escalation_engine=None):
        self.workspace_dir = workspace_dir
        self.evaluator = evaluator if evaluator is not None else TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = escalation_engine if escalation_engine is not None else IncidentAutoEscalationEngine()

    def handle_telemetry_and_respond(self, telemetry_payload: dict) -> dict:
        try:
            evaluation = self.evaluator.evaluate_with_incident_trigger(telemetry_payload)
            
            is_anomaly = evaluation.get("is_anomaly", False)
            incident_id = evaluation.get("incident_id")
            
            escalation_result = None
            if is_anomaly and incident_id:
                escalation_result = self.escalation_engine.process_escalation(incident_id)
                
            return {
                "anomaly_handled": bool(is_anomaly),
                "evaluation": evaluation,
                "escalation": escalation_result
            }
        except (AnomalyEvaluationException, InvalidTelemetryStreamException) as e:
            raise ConnectorException(str(e))
        except Exception as e:
            raise ConnectorException(str(e))

    def process_telemetry_stream(self, stream_io) -> dict:
        try:
            stream_result = self.evaluator.evaluate_stream_source(stream_io)
            incident_id = stream_result.get("incident_id")
            
            escalation_result = None
            if incident_id:
                escalation_result = self.escalation_engine.process_escalation(incident_id)
                
            return {
                "stream_result": stream_result,
                "escalation_result": escalation_result
            }
        except InvalidTelemetryStreamException as e:
            raise ConnectorException(str(e))
        except Exception as e:
            raise ConnectorException(str(e))

    def evaluate_and_mitigate_risks(self) -> dict:
        risk_assessment = self.escalation_engine.evaluate_system_telemetry_risks()
        patch_triggered = self.escalation_engine.check_and_trigger_patching()
        
        return {
            "risk_assessment": risk_assessment,
            "patch_triggered": patch_triggered
        }

    def process_incoming_stream(self, stream_data):
        import io
        stream_io = io.BytesIO(stream_data)
        return self.evaluator.evaluate_stream_source(stream_io)

    def verify_and_trigger_response(self) -> bool:
        return self.escalation_engine.check_and_trigger_patching()


def connect_telemetry_to_escalation(telemetry_payload: dict) -> dict:
    connector = TelemetryAnomalyResponseConnector()
    return connector.handle_telemetry_and_respond(telemetry_payload)