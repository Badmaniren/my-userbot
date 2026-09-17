import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import os

from skills.telemetry_anomaly_audit_bridge import (
    TelemetryAnomalyAuditBridge,
    AnomalyAuditBridgeException,
    AuditBridgeException
)


class TestTelemetryAnomalyAuditBridge(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"/tmp/{uuid.uuid4().hex}"
        self.lifecycle_mock = MagicMock()
        self.audit_reporter_mock = MagicMock()
        
        self.bridge = TelemetryAnomalyAuditBridge(
            workspace_dir=self.workspace_dir,
            lifecycle_bridge=self.lifecycle_mock,
            audit_reporter=self.audit_reporter_mock
        )

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            try:
                os.rmdir(self.workspace_dir)
            except OSError:
                pass

    def test_audit_health_after_incident_success(self):
        incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": incident_id, "metric": random.randint(100, 999)}
        epic_id = uuid.uuid4().hex
        stream = uuid.uuid4().hex

        self.lifecycle_mock.verify_and_close_lifecycle.return_value = True
        expected_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.audit_reporter_mock.generate_report.return_value = expected_report
        self.audit_reporter_mock.finalize_epic.return_value = True

        result = self.bridge.audit_health_after_incident(telemetry_payload, epic_id=epic_id, stream=stream)

        self.lifecycle_mock.process_lifecycle_event.assert_called_once_with(telemetry_payload)
        self.lifecycle_mock.verify_and_close_lifecycle.assert_called_once()
        self.audit_reporter_mock.generate_report.assert_called_once()
        self.audit_reporter_mock.finalize_epic.assert_called_once_with(epic_id, stream)

        self.assertTrue(result["lifecycle_closed"])
        self.assertEqual(result["audit_report"], expected_report)
        self.assertTrue(result["epic_finalized"])
        self.assertEqual(result["incident_id"], incident_id)

    def test_audit_health_after_incident_lifecycle_fail(self):
        telemetry_payload = {"incident_id": uuid.uuid4().hex}
        self.lifecycle_mock.verify_and_close_lifecycle.return_value = False

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.audit_health_after_incident(telemetry_payload)
        
        self.assertIn("Lifecycle verification failed", str(ctx.exception))

    def test_audit_health_after_incident_exception_handling(self):
        telemetry_payload = {"incident_id": uuid.uuid4().hex}
        error_msg = uuid.uuid4().hex
        self.lifecycle_mock.process_lifecycle_event.side_effect = Exception(error_msg)

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.audit_health_after_incident(telemetry_payload)

        self.assertIn("Failed to audit health after incident", str(ctx.exception))
        self.assertIn(error_msg, str(ctx.exception))

    def test_process_audit_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        self.audit_reporter_mock.export_summary.return_value = expected_summary

        result = self.bridge.process_audit_stream(stream_data)

        self.lifecycle_mock.process_lifecycle_stream.assert_called_once_with(stream_data)
        self.audit_reporter_mock.export_summary.assert_called_once()
        self.assertEqual(result, expected_summary)

    def test_process_audit_stream_exception(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        error_msg = uuid.uuid4().hex
        self.lifecycle_mock.process_lifecycle_stream.side_effect = Exception(error_msg)

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.process_audit_stream(stream_data)

        self.assertIn("Failed to process audit stream", str(ctx.exception))
        self.assertIn(error_msg, str(ctx.exception))

    def test_generate_epic_health_export(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        expected_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.audit_reporter_mock.generate_epic_report.return_value = expected_path

        result = self.bridge.generate_epic_health_export(payload, output_path)

        self.audit_reporter_mock.generate_epic_report.assert_called_once_with(payload, output_path)
        self.assertEqual(result, expected_path)

    def test_generate_epic_health_export_exception(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        error_msg = uuid.uuid4().hex
        self.audit_reporter_mock.generate_epic_report.side_effect = Exception(error_msg)

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.generate_epic_health_export(payload, output_path)

        self.assertIn("Failed to generate epic health export", str(ctx.exception))
        self.assertIn(error_msg, str(ctx.exception))

    def test_process_anomaly_and_audit_with_typeerror_fallback(self):
        incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": incident_id}
        audit_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        report_result = uuid.uuid4().hex

        self.audit_reporter_mock.generate_report.side_effect = TypeError("Unexpected argument")
        
        # Модифицируем мок, чтобы второй вызов без аргументов сработал
        def side_effect_func(*args, **kwargs):
            if args or kwargs:
                raise TypeError("Unexpected argument")
            return report_result

        self.audit_reporter_mock.generate_report.side_effect = side_effect_func

        result = self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

        self.lifecycle_mock.process_lifecycle_event.assert_called_once_with(telemetry_payload)
        self.assertEqual(result["audit_report"], report_result)
        self.assertEqual(result["lifecycle_status"], "PROCESSED")
        self.assertEqual(result["incident_id"], incident_id)

    def test_process_anomaly_and_audit_no_generate_report_method(self):
        incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": incident_id}
        audit_data = uuid.uuid4().hex

        del self.audit_reporter_mock.generate_report

        result = self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

        self.lifecycle_mock.process_lifecycle_event.assert_called_once_with(telemetry_payload)
        self.assertEqual(result["audit_report"], str(audit_data))
        self.assertEqual(result["lifecycle_status"], "PROCESSED")
        self.assertEqual(result["incident_id"], incident_id)

    def test_process_anomaly_and_audit_exception_raises_audit_bridge_exception(self):
        telemetry_payload = {"incident_id": uuid.uuid4().hex}
        audit_data = {}
        error_msg = uuid.uuid4().hex
        self.lifecycle_mock.process_lifecycle_event.side_effect = Exception(error_msg)

        with self.assertRaises(AuditBridgeException) as ctx:
            self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

        self.assertIn("Integration process failed", str(ctx.exception))
        self.assertIn(error_msg, str(ctx.exception))