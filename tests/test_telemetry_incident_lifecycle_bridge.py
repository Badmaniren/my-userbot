import unittest
from unittest.mock import MagicMock, patch
import os
import io
import uuid
import random
import string

from skills.telemetry_incident_lifecycle_bridge import (
    TelemetryIncidentLifecycleBridge,
    BridgeException,
    process_lifecycle_telemetry
)
from skills.telemetry_anomaly_evaluator_core import (
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)
from skills.telemetry_anomaly_response_connector import (
    ConnectorException
)


class TestTelemetryIncidentLifecycleBridge(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"test_workspace_{uuid.uuid4().hex}"
        self.mock_evaluator = MagicMock()
        self.mock_connector = MagicMock()

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            for root, dirs, files in os.walk(self.workspace_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.workspace_dir)

    def test_init_default_dependencies(self):
        bridge = TelemetryIncidentLifecycleBridge(workspace_dir=self.workspace_dir)
        self.assertEqual(bridge.workspace_dir, self.workspace_dir)
        self.assertIsNotNone(bridge.evaluator)
        self.assertIsNotNone(bridge.response_connector)

    def test_init_custom_dependencies(self):
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            evaluator=self.mock_evaluator,
            connector=self.mock_connector
        )
        self.assertEqual(bridge.evaluator, self.mock_evaluator)
        self.assertEqual(bridge.response_connector, self.mock_connector)
        self.assertEqual(bridge.response_connector.workspace_dir, self.workspace_dir)

    def test_process_lifecycle_event_success(self):
        source_id = uuid.uuid4().hex
        incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        lifecycle_status = f"STATUS_{uuid.uuid4().hex[:6].upper()}"
        
        telemetry_payload = {
            "source_id": source_id,
            "metric": random.randint(100, 999)
        }
        
        expected_response = {
            "incident_id": incident_id,
            "lifecycle_status": lifecycle_status
        }
        
        self.mock_connector.handle_telemetry_and_respond.return_value = expected_response
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        result = bridge.process_lifecycle_event(telemetry_payload)
        
        self.assertEqual(result["incident_id"], incident_id)
        self.assertEqual(result["lifecycle_status"], lifecycle_status)
        self.mock_connector.handle_telemetry_and_respond.assert_called_once_with(telemetry_payload)
        
        artifact_path = os.path.join(self.workspace_dir, f"incident_{source_id}.json")
        self.assertTrue(os.path.exists(artifact_path))

    def test_process_lifecycle_event_defaults_injected(self):
        source_id = uuid.uuid4().hex
        telemetry_payload = {
            "source_id": source_id,
            "data": ''.join(random.choices(string.ascii_letters, k=10))
        }
        
        self.mock_connector.handle_telemetry_and_respond.return_value = {}
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        result = bridge.process_lifecycle_event(telemetry_payload)
        
        self.assertEqual(result["incident_id"], f"incident_{source_id}")
        self.assertEqual(result["lifecycle_status"], "CLOSED_VIA_ESCALATION")

    def test_process_lifecycle_event_anomaly_exception(self):
        telemetry_payload = {"source_id": uuid.uuid4().hex}
        error_msg = f"Error anomaly {uuid.uuid4().hex}"
        self.mock_connector.handle_telemetry_and_respond.side_effect = AnomalyEvaluationException(error_msg)
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        with self.assertRaises(BridgeException) as ctx:
            bridge.process_lifecycle_event(telemetry_payload)
        
        self.assertIn(error_msg, str(ctx.exception))

    def test_process_lifecycle_event_connector_exception(self):
        telemetry_payload = {"source_id": uuid.uuid4().hex}
        error_msg = f"Connector failed {uuid.uuid4().hex}"
        self.mock_connector.handle_telemetry_and_respond.side_effect = ConnectorException(error_msg)
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        with self.assertRaises(BridgeException) as ctx:
            bridge.process_lifecycle_event(telemetry_payload)
        
        self.assertIn(error_msg, str(ctx.exception))

    def test_process_lifecycle_stream_success(self):
        stream_data = ''.join(random.choices(string.printable, k=50)).encode('utf-8')
        stream_io = io.BytesIO(stream_data)
        
        expected_output = {f"status_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        self.mock_connector.process_telemetry_stream.return_value = expected_output
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        result = bridge.process_lifecycle_stream(stream_io)
        
        self.assertEqual(result, expected_output)
        self.mock_connector.process_telemetry_stream.assert_called_once_with(stream_io)

    def test_process_lifecycle_stream_invalid_stream_exception(self):
        stream_io = io.BytesIO(b'')
        error_msg = f"Invalid stream {uuid.uuid4().hex}"
        self.mock_connector.process_telemetry_stream.side_effect = InvalidTelemetryStreamException(error_msg)
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        with self.assertRaises(BridgeException) as ctx:
            bridge.process_lifecycle_stream(stream_io)
            
        self.assertIn(error_msg, str(ctx.exception))

    def test_verify_and_close_lifecycle_success(self):
        expected_result = {f"verified_{uuid.uuid4().hex[:4]}": True}
        self.mock_connector.verify_and_trigger_response.return_value = expected_result
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        result = bridge.verify_and_close_lifecycle()
        
        self.assertEqual(result, expected_result)
        self.mock_connector.verify_and_trigger_response.assert_called_once()

    def test_verify_and_close_lifecycle_exception(self):
        error_msg = f"Verification failed {uuid.uuid4().hex}"
        self.mock_connector.verify_and_trigger_response.side_effect = ConnectorException(error_msg)
        
        bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            connector=self.mock_connector
        )
        
        with self.assertRaises(BridgeException) as ctx:
            bridge.verify_and_close_lifecycle()
            
        self.assertIn(error_msg, str(ctx.exception))

    def test_process_lifecycle_telemetry_function(self):
        source_id = uuid.uuid4().hex
        telemetry_payload = {"source_id": source_id}
        expected_response = {"incident_id": f"incident_{source_id}", "lifecycle_status": "CLOSED_VIA_ESCALATION"}
        
        with patch('skills.telemetry_incident_lifecycle_bridge.TelemetryIncidentLifecycleBridge') as MockBridgeClass:
            mock_instance = MockBridgeClass.return_value
            mock_instance.process_lifecycle_event.return_value = expected_response
            
            res = process_lifecycle_telemetry(telemetry_payload)
            
            MockBridgeClass.assert_called_once()
            mock_instance.process_lifecycle_event.assert_called_once_with(telemetry_payload)
            self.assertEqual(res, expected_response)