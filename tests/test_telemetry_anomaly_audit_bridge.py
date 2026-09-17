import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.telemetry_anomaly_audit_bridge import (
    TelemetryAnomalyAuditBridge,
    AnomalyAuditBridgeException
)


class TestTelemetryAnomalyAuditBridge(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"/tmp/{uuid.uuid4().hex}"
        self.bridge = TelemetryAnomalyAuditBridge(workspace_dir=self.workspace_dir)

    def test_initialization_and_dependencies(self):
        self.assertEqual(self.bridge.workspace_dir, self.workspace_dir)
        self.assertIsNotNone(self.bridge.lifecycle_bridge)
        self.assertIsNotNone(self.bridge.audit_reporter)

    @patch('skills.telemetry_anomaly_audit_bridge.TelemetryIncidentLifecycleBridge')
    @patch('skills.telemetry_anomaly_audit_bridge.DependencyAuditReporter')
    def test_audit_health_after_incident_success(self, mock_reporter_cls, mock_lifecycle_cls):
        mock_lifecycle_instance = mock_lifecycle_cls.return_value
        mock_reporter_instance = mock_reporter_cls.return_value

        rand_telemetry_id = uuid.uuid4().hex
        rand_audit_report_content = f"REPORT-{uuid.uuid4().hex}"
        rand_epic_id = uuid.uuid4().hex
        rand_stream_name = f"stream_{uuid.uuid4().hex}"

        mock_lifecycle_instance.verify_and_close_lifecycle.return_value = True
        mock_reporter_instance.generate_report.return_value = rand_audit_report_content
        mock_reporter_instance.finalize_epic.return_value = True

        bridge = TelemetryAnomalyAuditBridge(workspace_dir=self.workspace_dir)
        
        telemetry_payload = {
            "incident_id": rand_telemetry_id,
            "metric": random.choice(["cpu_load", "memory_leak", "latency_spike"]),
            "value": random.uniform(50.0, 100.0)
        }

        result = bridge.audit_health_after_incident(telemetry_payload, epic_id=rand_epic_id, stream=rand_stream_name)

        self.assertTrue(result["lifecycle_closed"])
        self.assertEqual(result["audit_report"], rand_audit_report_content)
        self.assertTrue(result["epic_finalized"])
        self.assertEqual(result["incident_id"], rand_telemetry_id)

        mock_lifecycle_instance.process_lifecycle_event.assert_called_once_with(telemetry_payload)
        mock_lifecycle_instance.verify_and_close_lifecycle.assert_called_once()
        mock_reporter_instance.generate_report.assert_called_once()
        mock_reporter_instance.finalize_epic.assert_called_once_with(rand_epic_id, rand_stream_name)

    @patch('skills.telemetry_anomaly_audit_bridge.TelemetryIncidentLifecycleBridge')
    def test_audit_health_lifecycle_failure(self, mock_lifecycle_cls):
        mock_lifecycle_instance = mock_lifecycle_cls.return_value
        mock_lifecycle_instance.verify_and_close_lifecycle.return_value = False

        rand_telemetry_id = uuid.uuid4().hex
        bridge = TelemetryAnomalyAuditBridge(workspace_dir=self.workspace_dir)

        telemetry_payload = {
            "incident_id": rand_telemetry_id,
            "status": "unresolved"
        }

        with self.assertRaises(AnomalyAuditBridgeException):
            bridge.audit_health_after_incident(telemetry_payload)

    @patch('skills.telemetry_anomaly_audit_bridge.TelemetryIncidentLifecycleBridge')
    @patch('skills.telemetry_anomaly_audit_bridge.DependencyAuditReporter')
    def test_process_audit_stream_handler(self, mock_reporter_cls, mock_lifecycle_cls):
        mock_lifecycle_instance = mock_lifecycle_cls.return_value
        mock_reporter_instance = mock_reporter_cls.return_value

        rand_stream_data = f"telemetry_data_{uuid.uuid4().hex}\n".encode('utf-8')
        stream_io = io.BytesIO(rand_stream_data)

        rand_epic_id = uuid.uuid4().hex
        rand_format = random.choice(["json", "xml", "pdf", "csv"])
        rand_summary_result = f"summary_{uuid.uuid4().hex}"

        mock_lifecycle_instance.process_lifecycle_stream.return_value = True
        mock_reporter_instance.export_summary.return_value = rand_summary_result

        bridge = TelemetryAnomalyAuditBridge(workspace_dir=self.workspace_dir)
        summary = bridge.process_audit_stream(stream_io, epic_id=rand_epic_id, export_format=rand_format)

        self.assertEqual(summary, rand_summary_result)
        mock_lifecycle_instance.process_lifecycle_stream.assert_called_once_with(stream_io)
        mock_reporter_instance.export_summary.assert_called_once()

    @patch('skills.telemetry_anomaly_audit_bridge.DependencyAuditReporter')
    def test_generate_epic_health_export_malformed(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        mock_reporter_instance.generate_epic_report.side_effect = Exception("Export failure")

        rand_output_path = f"/var/reports/{uuid.uuid4().hex}.json"
        rand_payload = {"audit_id": uuid.uuid4().hex, "score": random.randint(1, 100)}

        bridge = TelemetryAnomalyAuditBridge(workspace_dir=self.workspace_dir)

        with self.assertRaises(AnomalyAuditBridgeException):
            bridge.generate_epic_health_export(rand_payload, rand_output_path)