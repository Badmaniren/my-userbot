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
        self.lifecycle_bridge = MagicMock()
        self.audit_reporter = MagicMock()
        
        self.bridge = TelemetryAnomalyAuditBridge(
            workspace_dir=self.workspace_dir,
            lifecycle_bridge=self.lifecycle_bridge,
            audit_reporter=self.audit_reporter
        )

    def test_audit_health_after_incident_success(self):
        rand_incident_id = uuid.uuid4().hex
        rand_epic_id = uuid.uuid4().hex
        rand_stream = uuid.uuid4().hex
        rand_report = uuid.uuid4().hex

        telemetry_payload = {"incident_id": rand_incident_id}
        
        self.lifecycle_bridge.verify_and_close_lifecycle.return_value = True
        self.audit_reporter.generate_report.return_value = rand_report
        self.audit_reporter.finalize_epic.return_value = True

        result = self.bridge.audit_health_after_incident(
            telemetry_payload=telemetry_payload,
            epic_id=rand_epic_id,
            stream=rand_stream
        )

        self.assertTrue(result["lifecycle_closed"])
        self.assertEqual(result["audit_report"], rand_report)
        self.assertTrue(result["epic_finalized"])
        self.assertEqual(result["incident_id"], rand_incident_id)

        self.lifecycle_bridge.process_lifecycle_event.assert_called_once_with(telemetry_payload)
        self.lifecycle_bridge.verify_and_close_lifecycle.assert_called_once()
        self.audit_reporter.generate_report.assert_called_once()
        self.audit_reporter.finalize_epic.assert_called_once_with(rand_epic_id, rand_stream)

    def test_audit_health_after_incident_without_verify_method(self):
        rand_incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": rand_incident_id}
        
        del self.lifecycle_bridge.verify_and_close_lifecycle
        rand_report = uuid.uuid4().hex
        self.audit_reporter.generate_report.return_value = rand_report

        result = self.bridge.audit_health_after_incident(telemetry_payload=telemetry_payload)

        self.assertTrue(result["lifecycle_closed"])
        self.assertEqual(result["audit_report"], rand_report)
        self.assertFalse(result["epic_finalized"])
        self.assertEqual(result["incident_id"], rand_incident_id)

    def test_audit_health_after_incident_verification_failure(self):
        rand_incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": rand_incident_id}
        
        self.lifecycle_bridge.verify_and_close_lifecycle.return_value = False

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.audit_health_after_incident(telemetry_payload=telemetry_payload)

        self.assertIn("Lifecycle verification failed to close.", str(ctx.exception))

    def test_audit_health_after_incident_exception_handling(self):
        rand_incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": rand_incident_id}
        
        rand_error_msg = uuid.uuid4().hex
        self.lifecycle_bridge.process_lifecycle_event.side_effect = Exception(rand_error_msg)

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.audit_health_after_incident(telemetry_payload=telemetry_payload)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_process_audit_stream_success(self):
        rand_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_io = io.BytesIO(rand_stream_data)
        
        rand_epic_id = uuid.uuid4().hex
        rand_format = uuid.uuid4().hex
        rand_summary = uuid.uuid4().hex

        self.audit_reporter.export_summary.return_value = rand_summary

        result = self.bridge.process_audit_stream(
            stream_io=stream_io,
            epic_id=rand_epic_id,
            export_format=rand_format
        )

        self.assertEqual(result, rand_summary)
        self.lifecycle_bridge.process_lifecycle_stream.assert_called_once_with(stream_io)
        self.audit_reporter.export_summary.assert_called_once()

    def test_process_audit_stream_exception(self):
        stream_io = io.BytesIO(b"")
        rand_error_msg = uuid.uuid4().hex
        self.lifecycle_bridge.process_lifecycle_stream.side_effect = Exception(rand_error_msg)

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.process_audit_stream(stream_io=stream_io)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_generate_epic_health_export_success(self):
        rand_payload = {"key": uuid.uuid4().hex}
        rand_output_path = f"/tmp/{uuid.uuid4().hex}.json"
        rand_return_value = uuid.uuid4().hex

        self.audit_reporter.generate_epic_report.return_value = rand_return_value

        result = self.bridge.generate_epic_health_export(rand_payload, rand_output_path)

        self.assertEqual(result, rand_return_value)
        self.audit_reporter.generate_epic_report.assert_called_once_with(rand_payload, rand_output_path)

    def test_generate_epic_health_export_exception(self):
        rand_payload = {}
        rand_output_path = f"/tmp/{uuid.uuid4().hex}"
        rand_error_msg = uuid.uuid4().hex

        self.audit_reporter.generate_epic_report.side_effect = Exception(rand_error_msg)

        with self.assertRaises(AnomalyAuditBridgeException) as ctx:
            self.bridge.generate_epic_health_export(rand_payload, rand_output_path)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_process_anomaly_and_audit_with_typeerror_fallback(self):
        rand_incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": rand_incident_id}
        audit_data = {"audit": uuid.uuid4().hex}
        rand_report = uuid.uuid4().hex

        self.audit_reporter.generate_report.side_effect = TypeError("Unexpected argument")
        
        # Модифицируем мок, чтобы вторая попытка (без аргументов) сработала успешно
        # Так как generate_report вызывается дважды или один раз с ошибкой и ловлей внутри:
        # В коде:
        # try: audit_report = self.audit_reporter.generate_report(audit_data)
        # except TypeError: audit_report = self.audit_reporter.generate_report()
        
        # Настроим side_effect так: первый вызов падает с TypeError, второй возвращает rand_report
        self.audit_reporter.generate_report.side_effect = [TypeError("mismatch"), rand_report]

        result = self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

        self.assertEqual(result["audit_report"], rand_report)
        self.assertEqual(result["lifecycle_status"], "PROCESSED")
        self.assertEqual(result["incident_id"], rand_incident_id)
        self.lifecycle_bridge.process_lifecycle_event.assert_called_once_with(telemetry_payload)

    def test_process_anomaly_and_audit_without_generate_report_method(self):
        rand_incident_id = uuid.uuid4().hex
        telemetry_payload = {"incident_id": rand_incident_id}
        audit_data = f"audit_str_{uuid.uuid4().hex}"

        del self.audit_reporter.generate_report

        result = self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

        self.assertEqual(result["audit_report"], str(audit_data))
        self.assertEqual(result["lifecycle_status"], "PROCESSED")
        self.assertEqual(result["incident_id"], rand_incident_id)

    def test_process_anomaly_and_audit_exception_raises_audit_bridge_exception(self):
        telemetry_payload = {"incident_id": uuid.uuid4().hex}
        audit_data = {}
        rand_error_msg = uuid.uuid4().hex

        self.lifecycle_bridge.process_lifecycle_event.side_effect = Exception(rand_error_msg)

        with self.assertRaises(AuditBridgeException) as ctx:
            self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

        self.assertIn(rand_error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()