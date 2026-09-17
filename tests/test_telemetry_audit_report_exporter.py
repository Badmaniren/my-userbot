import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.telemetry_audit_report_exporter import (
    TelemetryAuditReportExporter,
    TelemetryAuditReportExporterException
)
from skills.telemetry_anomaly_audit_bridge import TelemetryAnomalyAuditBridge
from skills.recovery_report_exporter import RecoveryReportExporter


class TestTelemetryAuditReportExporter(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"/tmp/{uuid.uuid4().hex}"
        self.lifecycle_bridge = MagicMock()
        self.audit_reporter = MagicMock()
        
        self.anomaly_bridge = TelemetryAnomalyAuditBridge(
            workspace_dir=self.workspace_dir,
            lifecycle_bridge=self.lifecycle_bridge,
            audit_reporter=self.audit_reporter
        )
        self.recovery_exporter = RecoveryReportExporter()
        
        self.exporter = TelemetryAuditReportExporter(
            anomaly_bridge=self.anomaly_bridge,
            recovery_exporter=self.recovery_exporter
        )

    def test_export_audit_and_recovery_report_success(self):
        random_epic_id = f"epic-{uuid.uuid4().hex[:8]}"
        random_stream_data = f"stream-content-{uuid.uuid4().hex}".encode('utf-8')
        random_stream = io.BytesIO(random_stream_data)
        random_format = random.choice(['json', 'xml', 'yaml', 'pdf'])
        
        random_module = f"module_{uuid.uuid4().hex[:6]}"
        random_exc_msg = f"Error_{uuid.uuid4().hex[:6]}"
        try:
            raise RuntimeError(random_exc_msg)
        except RuntimeError as e:
            random_exc = e
            random_traceback = f"Traceback at {uuid.uuid4().hex}"
            
        random_incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        random_audit_data = {
            "key": uuid.uuid4().hex,
            "value": random.randint(100, 999)
        }
        
        mock_audit_result = f"audit-result-{uuid.uuid4().hex}"
        mock_report_result = f"report-result-{uuid.uuid4().hex}"

        with patch.object(self.anomaly_bridge, 'process_audit_stream', return_value=mock_audit_result) as mock_process, \
             patch.object(self.recovery_exporter, 'generate_comprehensive_report', return_value=mock_report_result) as mock_gen_report:

            result = self.exporter.export_audit_and_recovery_report(
                epic_id=random_epic_id,
                stream=random_stream,
                export_format=random_format,
                module_name=random_module,
                exception=random_exc,
                traceback_str=random_traceback,
                incident_id=random_incident_id,
                audit_data=random_audit_data
            )

            mock_process.assert_called_once_with(random_stream, random_epic_id, random_format)
            mock_gen_report.assert_called_once_with(
                module_name=random_module,
                exception=random_exc,
                traceback_str=random_traceback,
                incident_id=random_incident_id,
                audit_data=random_audit_data
            )
            
            self.assertIn(mock_audit_result, result.values())
            self.assertIn(mock_report_result, result.values())
            self.assertEqual(result['epic_id'], random_epic_id)
            self.assertEqual(result['export_format'], random_format)

    def test_export_audit_and_recovery_report_failure(self):
        random_epic_id = f"epic-{uuid.uuid4().hex[:8]}"
        random_stream = io.BytesIO(b"corrupted-stream")
        random_format = "json"
        
        random_module = "test_mod"
        random_exc = ValueError("bad value")
        random_traceback = "tb"
        random_incident_id = "inc-1"
        random_audit_data = {}

        with patch.object(self.anomaly_bridge, 'process_audit_stream', side_effect=Exception("Bridge failure")):
            with self.assertRaises(TelemetryAuditReportExporterException) as ctx:
                self.exporter.export_audit_and_recovery_report(
                    epic_id=random_epic_id,
                    stream=random_stream,
                    export_format=random_format,
                    module_name=random_module,
                    exception=random_exc,
                    traceback_str=random_traceback,
                    incident_id=random_incident_id,
                    audit_data=random_audit_data
                )
            self.assertIn("Bridge failure", str(ctx.exception))

    def test_finalize_epic_audit_export(self):
        random_epic_id = f"epic-{uuid.uuid4().hex[:8]}"
        random_output_path = f"/var/reports/{uuid.uuid4().hex}.json"
        random_payload_key = uuid.uuid4().hex
        random_payload_val = random.randint(1, 1000)
        random_payload = {random_payload_key: random_payload_val}

        mock_export_res = f"path/to/exported/{uuid.uuid4().hex}"

        with patch.object(self.anomaly_bridge, 'generate_epic_health_export', return_value=mock_export_res) as mock_gen_health:
            result = self.exporter.finalize_epic_audit_export(
                payload=random_payload,
                output_path=random_output_path
            )

            mock_gen_health.assert_called_once_with(random_payload, random_output_path)
            self.assertEqual(result, mock_export_res)

    def test_finalize_epic_audit_export_failure(self):
        random_output_path = f"/var/reports/{uuid.uuid4().hex}.json"
        random_payload = {"test": "data"}

        with patch.object(self.anomaly_bridge, 'generate_epic_health_export', side_effect=Exception("Export failed")):
            with self.assertRaises(TelemetryAuditReportExporterException) as ctx:
                self.exporter.finalize_epic_audit_export(
                    payload=random_payload,
                    output_path=random_output_path
                )
            self.assertIn("Export failed", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()