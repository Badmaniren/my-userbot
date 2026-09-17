import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.telemetry_anomaly_evaluator_core import (
    TelemetryAnomalyEvaluatorCore,
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)
from skills.telemetry_anomaly_response_connector import (
    TelemetryAnomalyResponseConnector,
    ConnectorException
)
from skills.telemetry_incident_lifecycle_bridge import (
    TelemetryIncidentLifecycleBridge,
    BridgeException
)


class TestTelemetryIncidentLifecycleBridgeArchitect(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"/tmp/{uuid.uuid4().hex}"
        self.mock_evaluator = MagicMock(spec=TelemetryAnomalyEvaluatorCore)
        self.mock_escalation_engine = MagicMock()
        
        self.bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            evaluator=self.mock_evaluator,
            escalation_engine=self.mock_escalation_engine
        )

    def test_bridge_initialization_composition(self):
        self.assertIsInstance(self.bridge.evaluator, TelemetryAnomalyEvaluatorCore)
        self.assertIsNotNone(self.bridge.response_connector)
        self.assertIsInstance(self.bridge.response_connector, TelemetryAnomalyResponseConnector)
        self.assertEqual(self.bridge.workspace_dir, self.workspace_dir)

    def test_process_lifecycle_success(self):
        random_telemetry_key = uuid.uuid4().hex
        random_telemetry_value = random.randint(1000, 99999)
        random_incident_id = uuid.uuid4().hex
        
        telemetry_payload = {
            random_telemetry_key: random_telemetry_value,
            "metric_name": "".join(random.choices(string.ascii_lowercase, k=10))
        }

        expected_response = {
            "status": "escalated",
            "incident_id": random_incident_id,
            "eval_result": "anomaly_detected"
        }

        with patch.object(
            TelemetryAnomalyResponseConnector,
            "handle_telemetry_and_respond",
            return_value=expected_response
        ) as mock_handle:
            
            result = self.bridge.process_lifecycle_event(telemetry_payload)
            
            mock_handle.assert_called_once_with(telemetry_payload)
            self.assertEqual(result["incident_id"], random_incident_id)
            self.assertEqual(result["status"], "escalated")

    def test_process_lifecycle_stream_source(self):
        random_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")
        stream_io = io.BytesIO(random_stream_data)
        
        random_result_id = uuid.uuid4().hex
        expected_stream_response = {
            "stream_processed": True,
            "lifecycle_id": random_result_id
        }

        with patch.object(
            TelemetryAnomalyResponseConnector,
            "process_telemetry_stream",
            return_value=expected_stream_response
        ) as mock_stream_proc:
            
            result = self.bridge.process_lifecycle_stream(stream_io)
            
            mock_stream_proc.assert_called_once_with(stream_io)
            self.assertEqual(result["lifecycle_id"], random_result_id)
            self.assertTrue(result["stream_processed"])

    def test_bridge_handles_evaluator_exception(self):
        random_error_msg = uuid.uuid4().hex
        telemetry_payload = {uuid.uuid4().hex: random.random()}

        with patch.object(
            TelemetryAnomalyResponseConnector,
            "handle_telemetry_and_respond",
            side_effect=AnomalyEvaluationException(random_error_msg)
        ):
            with self.assertRaises(BridgeException) as ctx:
                self.bridge.process_lifecycle_event(telemetry_payload)
            
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_bridge_handles_connector_exception(self):
        random_error_msg = uuid.uuid4().hex
        telemetry_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(
            TelemetryAnomalyResponseConnector,
            "handle_telemetry_and_respond",
            side_effect=ConnectorException(random_error_msg)
        ):
            with self.assertRaises(BridgeException) as ctx:
                self.bridge.process_lifecycle_event(telemetry_payload)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_verify_and_close_lifecycle(self):
        random_check_status = random.choice([True, False])

        with patch.object(
            TelemetryAnomalyResponseConnector,
            "verify_and_trigger_response",
            return_value=random_check_status
        ) as mock_verify:
            
            result = self.bridge.verify_and_close_lifecycle()
            
            mock_verify.assert_called_once()
            self.assertEqual(result, random_check_status)


if __name__ == "__main__":
    unittest.main()