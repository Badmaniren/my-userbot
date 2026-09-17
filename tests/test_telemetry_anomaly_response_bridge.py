import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string

from skills.telemetry_anomaly_response_bridge import (
    TelemetryAnomalyResponseBridge,
    auto_escalate_incident
)
from skills.telemetry_anomaly_evaluator_core import AnomalyEvaluationException


class TestTelemetryAnomalyResponseBridge(unittest.TestCase):

    def setUp(self):
        self.random_error_message = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
        self.incident_id_val = uuid.uuid4().hex
        self.severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.workspace_val = uuid.uuid4().hex

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    @patch('skills.telemetry_anomaly_response_bridge.TelemetryAnomalyEvaluatorCore')
    def test_bridge_initialization(self, mock_evaluator_cls, mock_escalation_cls):
        bridge = TelemetryAnomalyResponseBridge()
        self.assertIsNotNone(bridge.evaluator)
        self.assertIsNotNone(bridge.escalation_engine)
        mock_evaluator_cls.assert_called_once()
        mock_escalation_cls.assert_called_once()

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    @patch('skills.telemetry_anomaly_response_bridge.TelemetryAnomalyEvaluatorCore')
    def test_process_anomaly_with_escalation(self, mock_evaluator_cls, mock_escalation_cls):
        mock_evaluator_instance = mock_evaluator_cls.return_value
        mock_escalation_instance = mock_escalation_cls.return_value

        expected_eval = {
            "is_anomaly": True,
            "incident_id": self.incident_id_val,
            "metric": ''.join(random.choices(string.ascii_lowercase, k=10))
        }
        expected_escalation = {
            "escalated": True,
            "status": "triggered",
            "ref": uuid.uuid4().hex
        }

        mock_evaluator_instance.evaluate.return_value = expected_eval
        mock_escalation_instance.process_escalation.return_value = expected_escalation

        bridge = TelemetryAnomalyResponseBridge()
        payload = {"metric_value": random.randint(1, 1000)}
        result = bridge.handle_telemetry_and_respond(payload)

        mock_evaluator_instance.evaluate.assert_called_once_with(payload)
        mock_escalation_instance.process_escalation.assert_called_once_with(self.incident_id_val)

        self.assertEqual(result["evaluation"], expected_eval)
        self.assertEqual(result["escalation"], expected_escalation)

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    @patch('skills.telemetry_anomaly_response_bridge.TelemetryAnomalyEvaluatorCore')
    def test_process_anomaly_no_escalation_needed(self, mock_evaluator_cls, mock_escalation_cls):
        mock_evaluator_instance = mock_evaluator_cls.return_value
        mock_escalation_instance = mock_escalation_cls.return_value

        expected_eval = {
            "is_anomaly": False,
            "incident_id": None
        }

        mock_evaluator_instance.evaluate.return_value = expected_eval

        bridge = TelemetryAnomalyResponseBridge()
        payload = {"metric_value": random.randint(1, 1000)}
        result = bridge.handle_telemetry_and_respond(payload)

        mock_evaluator_instance.evaluate.assert_called_once_with(payload)
        mock_escalation_instance.process_escalation.assert_not_called()

        self.assertEqual(result["evaluation"], expected_eval)
        self.assertIsNone(result["escalation"])

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    @patch('skills.telemetry_anomaly_response_bridge.TelemetryAnomalyEvaluatorCore')
    def test_stream_anomaly_handling(self, mock_evaluator_cls, mock_escalation_cls):
        mock_evaluator_instance = mock_evaluator_cls.return_value
        mock_escalation_instance = mock_escalation_cls.return_value

        expected_stream_eval = {
            "anomaly_detected": True,
            "score": random.random()
        }

        mock_evaluator_instance.evaluate_stream_source.return_value = expected_stream_eval
        mock_escalation_instance.check_and_trigger_patching.return_value = True

        bridge = TelemetryAnomalyResponseBridge()
        stream_source = MagicMock()
        result = bridge.process_stream_and_mitigate(stream_source)

        mock_evaluator_instance.evaluate_stream_source.assert_called_once_with(stream_source)
        mock_escalation_instance.check_and_trigger_patching.assert_called_once()

        self.assertTrue(result["stream_evaluated"])
        self.assertTrue(result["patching_triggered"])

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    @patch('skills.telemetry_anomaly_response_bridge.TelemetryAnomalyEvaluatorCore')
    def test_anomaly_evaluation_exception_handling(self, mock_evaluator_cls, mock_escalation_cls):
        mock_evaluator_instance = mock_evaluator_cls.return_value
        mock_evaluator_instance.evaluate.side_effect = AnomalyEvaluationException(self.random_error_message)

        bridge = TelemetryAnomalyResponseBridge()
        payload = {"invalid_key": uuid.uuid4().hex}

        with self.assertRaises(AnomalyEvaluationException) as ctx:
            bridge.handle_telemetry_and_respond(payload)

        self.assertIn(self.random_error_message, str(ctx.exception))
        mock_evaluator_instance.evaluate.assert_called_once_with(payload)

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    def test_auto_escalate_incident_helper_with_dict(self, mock_escalation_cls):
        mock_engine_instance = mock_escalation_cls.return_value
        expected_dict_result = {
            "status": uuid.uuid4().hex,
            "incident_id": self.incident_id_val,
            "processed": True
        }
        mock_engine_instance.process_escalation.return_value = expected_dict_result

        result = auto_escalate_incident(self.incident_id_val, severity=self.severity_val, workspace_dir=self.workspace_val)

        mock_escalation_cls.assert_called_once()
        mock_engine_instance.process_escalation.assert_called_once_with(self.incident_id_val)
        self.assertEqual(result, expected_dict_result)

    @patch('skills.telemetry_anomaly_response_bridge.IncidentAutoEscalationEngine')
    def test_auto_escalate_incident_helper_fallback(self, mock_escalation_cls):
        mock_engine_instance = mock_escalation_cls.return_value
        mock_engine_instance.process_escalation.return_value = None

        result = auto_escalate_incident(self.incident_id_val, severity=self.severity_val, workspace_dir=self.workspace_val)

        mock_escalation_cls.assert_called_once()
        mock_engine_instance.process_escalation.assert_called_once_with(self.incident_id_val)

        expected_fallback = {
            "status": "success",
            "incident_id": self.incident_id_val,
            "severity": self.severity_val
        }
        self.assertEqual(result, expected_fallback)


if __name__ == '__main__':
    unittest.main()