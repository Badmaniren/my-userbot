import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.telemetry_anomaly_response_connector import (
    TelemetryAnomalyResponseConnector,
    ConnectorException
)
from skills.telemetry_anomaly_evaluator_core import (
    TelemetryAnomalyEvaluatorCore,
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine

class TestTelemetryAnomalyResponseConnector(unittest.TestCase):

    def setUp(self):
        self.workspace = "".join(random.choices(string.ascii_lowercase, k=10))
        self.connector = TelemetryAnomalyResponseConnector(workspace_dir=self.workspace)

    def test_initialization_success(self):
        self.assertIsInstance(self.connector.evaluator, TelemetryAnomalyEvaluatorCore)
        self.assertIsInstance(self.connector.escalation_engine, IncidentAutoEscalationEngine)
        self.assertEqual(self.connector.workspace_dir, self.workspace)

    def test_process_telemetry_flow_anomaly_detected_and_escalated(self):
        random_telemetry_key = uuid.uuid4().hex
        random_telemetry_val = random.randint(100, 9999)
        random_incident_id = uuid.uuid4().hex
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        telemetry_payload = {
            random_telemetry_key: random_telemetry_val,
            "metric": "".join(random.choices(string.ascii_letters, k=8))
        }
        
        evaluation_result = {
            "is_anomaly": True,
            "incident_id": random_incident_id,
            "severity": random_severity,
            "details": uuid.uuid4().hex
        }
        
        escalation_result = {
            "status": "ESCALATED",
            "incident_id": random_incident_id,
            "timestamp": random.randint(1000000, 9999999)
        }

        with patch.object(TelemetryAnomalyEvaluatorCore, 'evaluate_with_incident_trigger', return_value=evaluation_result) as mock_eval, \
             patch.object(IncidentAutoEscalationEngine, 'process_escalation', return_value=escalation_result) as mock_esc:

            result = self.connector.handle_telemetry_and_respond(telemetry_payload)

            mock_eval.assert_called_once_with(telemetry_payload)
            mock_esc.assert_called_once_with(random_incident_id)

            self.assertTrue(result["anomaly_handled"])
            self.assertEqual(result["evaluation"], evaluation_result)
            self.assertEqual(result["escalation"], escalation_result)

    def test_process_telemetry_flow_no_anomaly(self):
        random_telemetry_key = uuid.uuid4().hex
        random_telemetry_val = random.randint(1, 99)
        
        telemetry_payload = {
            random_telemetry_key: random_telemetry_val,
            "status": "normal"
        }
        
        evaluation_result = {
            "is_anomaly": False,
            "incident_id": None,
            "severity": "NONE"
        }

        with patch.object(TelemetryAnomalyEvaluatorCore, 'evaluate_with_incident_trigger', return_value=evaluation_result) as mock_eval, \
             patch.object(IncidentAutoEscalationEngine, 'process_escalation') as mock_esc:

            result = self.connector.handle_telemetry_and_respond(telemetry_payload)

            mock_eval.assert_called_once_with(telemetry_payload)
            mock_esc.assert_not_called()

            self.assertFalse(result["anomaly_handled"])
            self.assertEqual(result["evaluation"], evaluation_result)
            self.assertIsNone(result["escalation"])

    def test_stream_source_processing_success(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        stream_io = io.BytesIO(random_bytes)
        
        random_incident_id = uuid.uuid4().hex
        stream_evaluation = {
            "stream_status": "PROCESSED",
            "detected_anomalies": 1,
            "incident_id": random_incident_id
        }
        
        escalation_response = {
            "escalation_id": uuid.uuid4().hex,
            "dispatched": True
        }

        with patch.object(TelemetryAnomalyEvaluatorCore, 'evaluate_stream_source', return_value=stream_evaluation) as mock_stream_eval, \
             patch.object(IncidentAutoEscalationEngine, 'process_escalation', return_value=escalation_response) as mock_esc:

            result = self.connector.process_telemetry_stream(stream_io)

            mock_stream_eval.assert_called_once_with(stream_io)
            mock_esc.assert_called_once_with(random_incident_id)

            self.assertEqual(result["stream_result"], stream_evaluation)
            self.assertEqual(result["escalation_result"], escalation_response)

    def test_evaluator_exception_handling(self):
        random_telemetry_key = uuid.uuid4().hex
        telemetry_payload = {random_telemetry_key: random.randint(1000, 5000)}
        random_error_msg = uuid.uuid4().hex

        with patch.object(TelemetryAnomalyEvaluatorCore, 'evaluate_with_incident_trigger', side_effect=AnomalyEvaluationException(random_error_msg)):
            with self.assertRaises(ConnectorException) as ctx:
                self.connector.handle_telemetry_and_respond(telemetry_payload)
            
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_invalid_telemetry_stream_exception_handling(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        stream_io = io.BytesIO(random_bytes)
        random_error_msg = uuid.uuid4().hex

        with patch.object(TelemetryAnomalyEvaluatorCore, 'evaluate_stream_source', side_effect=InvalidTelemetryStreamException(random_error_msg)):
            with self.assertRaises(ConnectorException) as ctx:
                self.connector.process_telemetry_stream(stream_io)
            
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_system_telemetry_risk_assessment_and_patching(self):
        random_risk_score = random.uniform(0.1, 0.99)
        risk_evaluation_data = {
            "risk_score": random_risk_score,
            "requires_patch": True
        }
        patch_triggered = random.choice([True, False])

        with patch.object(IncidentAutoEscalationEngine, 'evaluate_system_telemetry_risks', return_value=risk_evaluation_data) as mock_risk_eval, \
             patch.object(IncidentAutoEscalationEngine, 'check_and_trigger_patching', return_value=patch_triggered) as mock_patch:

            result = self.connector.evaluate_and_mitigate_risks()

            mock_risk_eval.assert_called_once()
            mock_patch.assert_called_once()

            self.assertEqual(result["risk_assessment"], risk_evaluation_data)
            self.assertEqual(result["patch_triggered"], patch_triggered)

    def unexpected_error_raises_connector_exception(self):
        random_telemetry_key = uuid.uuid4().hex
        telemetry_payload = {random_telemetry_key: uuid.uuid4().hex}
        random_runtime_error = uuid.uuid4().hex

        with patch.object(TelemetryAnomalyEvaluatorCore, 'evaluate_with_incident_trigger', side_effect=RuntimeError(random_runtime_error)):
            with self.assertRaises(ConnectorException) as ctx:
                self.connector.handle_telemetry_and_respond(telemetry_payload)
            
            self.assertIn(random_runtime_error, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()