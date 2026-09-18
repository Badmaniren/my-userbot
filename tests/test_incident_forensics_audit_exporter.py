import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_forensics_audit_exporter import (
    IncidentForensicsAuditExporter,
    IncidentForensicsAuditExporterException
)

class TestIncidentForensicsAuditExporter(unittest.TestCase):

    def setUp(self):
        self.mock_collector = MagicMock()
        self.mock_exporter = MagicMock()
        self.exporter_instance = IncidentForensicsAuditExporter(
            audit_trail_collector=self.mock_collector,
            telemetry_audit_report_exporter=self.mock_exporter
        )

    def test_compose_forensics_evidence_success(self):
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
        incident_id = f"inc-{uuid.uuid4().hex}-{random_suffix}"
        destination_path = f"/var/log/forensics/{uuid.uuid4().hex}.json"
        include_raw = random.choice([True, False])

        epic_id = f"epic-{uuid.uuid4().hex}"
        stream_name = f"stream-{uuid.uuid4().hex}"
        export_format = random.choice(["json", "csv", "xml"])
        module_name = f"mod-{uuid.uuid4().hex}"
        output_path = f"/var/reports/{uuid.uuid4().hex}.pdf"

        expected_audit_trail = {
            "incident_id": incident_id,
            "status": "collected",
            "random_token": uuid.uuid4().hex
        }
        self.mock_collector.collect_incident_audit_trail.return_value = expected_audit_trail

        expected_export_result = {
            "status": "exported",
            "epic_id": epic_id,
            "path": output_path
        }
        self.mock_exporter.process_and_export_audit_report.return_value = expected_export_result

        with patch('skills.incident_forensics_audit_exporter.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')

            telemetry_payload = {"stream": stream_name, "data": random.randint(100, 999)}

            result = self.exporter_instance.compose_forensics_evidence(
                incident_data={"id": incident_id},
                destination_path=destination_path,
                include_raw_telemetry=include_raw,
                telemetry_payload=telemetry_payload,
                epic_id=epic_id,
                export_format=export_format,
                module_name=module_name,
                output_path=output_path
            )

        self.mock_collector.collect_incident_audit_trail.assert_called_once_with(
            {"id": incident_id}, destination_path, include_raw
        )

        self.mock_exporter.process_and_export_audit_report.assert_called_once_with(
            telemetry_payload=telemetry_payload,
            audit_data=expected_audit_trail,
            epic_id=epic_id,
            incident_id=incident_id,
            module_name=module_name,
            output_path=output_path
        )

        self.assertIn("audit_trail", result)
        self.assertIn("export_report", result)
        self.assertEqual(result["audit_trail"], expected_audit_trail)
        self.assertEqual(result["export_report"], expected_export_result)

    def test_compose_forensics_evidence_collector_failure(self):
        random_error_msg = f"err-{uuid.uuid4().hex}"
        incident_id = f"inc-{uuid.uuid4().hex}"
        destination_path = f"/tmp/{uuid.uuid4().hex}"

        self.mock_collector.collect_incident_audit_trail.side_effect = Exception(random_error_msg)

        with self.assertRaises(IncidentForensicsAuditExporterException) as ctx:
            self.exporter_instance.compose_forensics_evidence(
                incident_data={"id": incident_id},
                destination_path=destination_path,
                include_raw_telemetry=True,
                telemetry_payload={},
                epic_id="e-1",
                export_format="json",
                module_name="m-1",
                output_path="/tmp/out.json"
            )

        self.assertIn(random_error_msg, str(ctx.exception))
        self.mock_exporter.process_and_export_audit_report.assert_not_called()

    def test_finalize_package_evidence(self):
        payload_data = {
            "evidence_id": uuid.uuid4().hex,
            "hash": ''.join(random.choices(string.hexdigits, k=32))
        }
        output_path = f"/secure/vault/{uuid.uuid4().hex}.zip"

        expected_final_result = {
            "finalized": True,
            "destination": output_path
        }
        self.mock_exporter.finalize_epic_audit_export.return_value = expected_final_result

        result = self.exporter_instance.finalize_package_evidence(
            payload=payload_data,
            output_path=output_path
        )

        self.mock_exporter.finalize_epic_audit_export.assert_called_once_with(
            payload=payload_data,
            output_path=output_path
        )
        self.assertEqual(result, expected_final_result)

    def test_start_new_stub(self):
        with patch('skills.incident_forensics_audit_exporter.incident_audit_trail_collector') as mock_iatc:
            IncidentForensicsAuditExporter.start_new()
            mock_iatc.start_new.assert_called_once()

    def test_io_stream_handling_in_forensics(self):
        random_bytes = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        incident_id = f"inc-{uuid.uuid4().hex}"
        destination_path = f"/var/{uuid.uuid4().hex}"

        self.mock_collector.collect_incident_audit_trail.return_value = {"stream_data": random_bytes.read().decode('utf-8')}
        self.mock_exporter.process_and_export_audit_report.return_value = {"status": "ok"}

        result = self.exporter_instance.compose_forensics_evidence(
            incident_data={"id": incident_id},
            destination_path=destination_path,
            include_raw_telemetry=False,
            telemetry_payload={"blob": random_bytes},
            epic_id=uuid.uuid4().hex,
            export_format="raw",
            module_name=uuid.uuid4().hex,
            output_path=destination_path
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["export_report"]["status"], "ok")