import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.incident_forensics_audit_archiver import (
    incident_forensics_audit_archiver,
    IncidentForensicsAuditArchiver
)

class TestIncidentForensicsAuditArchiver(unittest.TestCase):

    def setUp(self):
        self.rand_incident_id = uuid.uuid4().hex
        self.rand_destination = f"/var/log/forensics/{uuid.uuid4().hex}.zip"
        self.rand_module_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_epic_id = f"EPIC-{random.randint(1000, 9999)}"
        self.rand_stream = io.BytesIO(uuid.uuid4().bytes + b"random_stream_data")
        self.rand_export_format = random.choice(["json", "pdf", "csv", "xml"])

        self.rand_incident_data = {
            "id": self.rand_incident_id,
            "severity": random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
            "vector": uuid.uuid4().hex
        }
        self.rand_audit_data = {
            "telemetry_nodes": random.randint(5, 150),
            "status": "COMPROMISED"
        }
        self.rand_summary_payload = {
            "summary_code": random.randint(10000, 99999),
            "details": uuid.uuid4().hex
        }
        self.rand_report_payload = {
            "forensic_id": uuid.uuid4().hex,
            "metrics": [random.random() for _ in range(3)]
        }
        self.rand_output_path = f"/tmp/{uuid.uuid4().hex}_report.json"

        self.exception_msg = uuid.uuid4().hex
        self.rand_exception = RuntimeError(self.exception_msg)
        self.rand_traceback_str = f"Traceback (most recent call last):\n  File '{uuid.uuid4().hex}.py', line {random.randint(1, 100)}\n    raise RuntimeError"

    def test_composition_imports_and_instantiation(self):
        archiver_instance = IncidentForensicsAuditArchiver()
        self.assertIsNotNone(archiver_instance)

        with patch('skills.incident_forensics_audit_archiver.incident_audit_trail_collector') as mock_collector, \
             patch('skills.incident_forensics_audit_archiver.RecoveryReportExporter') as mock_exporter_cls:

            mock_exporter_instance = mock_exporter_cls.return_value

            mock_collector.collect_incident_audit_trail.return_value = {
                "collected": True,
                "path": self.rand_destination
            }

            mock_exporter_instance.generate_comprehensive_report.return_value = {
                "report_status": "GENERATED",
                "id": self.rand_incident_id
            }

            archiver = IncidentForensicsAuditArchiver()
            result = archiver.archive_incident(
                incident_data=self.rand_incident_data,
                destination_path=self.rand_destination,
                include_raw_telemetry=True,
                module_name=self.rand_module_name,
                exception=self.rand_exception,
                traceback_str=self.rand_traceback_str
            )

            mock_collector.collect_incident_audit_trail.assert_called_once_with(
                self.rand_incident_data,
                self.rand_destination,
                True
            )
            mock_exporter_instance.generate_comprehensive_report.assert_called_once_with(
                self.rand_module_name,
                self.rand_exception,
                self.rand_traceback_str,
                self.rand_incident_id,
                self.rand_incident_data
            )
            self.assertEqual(result["incident_id"], self.rand_incident_id)

    def test_finalize_and_export_summary_delegation(self):
        with patch('skills.incident_forensics_audit_archiver.RecoveryReportExporter') as mock_exporter_cls:
            mock_exporter_instance = mock_exporter_cls.return_value
            expected_export_result = {
                "exported": True,
                "format": self.rand_export_format,
                "epic": self.rand_epic_id
            }
            mock_exporter_instance.finalize_and_export_summary.return_value = expected_export_result

            archiver = IncidentForensicsAuditArchiver()
            res = archiver.finalize_archive_summary(
                epic_id=self.rand_epic_id,
                stream=self.rand_stream,
                summary_payload=self.rand_summary_payload,
                export_format=self.rand_export_format
            )

            mock_exporter_instance.finalize_and_export_summary.assert_called_once_with(
                self.rand_epic_id,
                self.rand_stream,
                self.rand_summary_payload,
                self.rand_export_format
            )
            self.assertEqual(res, expected_export_result)

    def test_export_epic_report_file_delegation(self):
        with patch('skills.incident_forensics_audit_archiver.RecoveryReportExporter') as mock_exporter_cls:
            mock_exporter_instance = mock_exporter_cls.return_value
            mock_exporter_instance.export_epic_report_file.return_value = self.rand_output_path

            archiver = IncidentForensicsAuditArchiver()
            res = archiver.export_archive_file(
                report_payload=self.rand_report_payload,
                output_path=self.rand_output_path
            )

            mock_exporter_instance.export_epic_report_file.assert_called_once_with(
                self.rand_report_payload,
                self.rand_output_path
            )
            self.assertEqual(res, self.rand_output_path)

    def test_module_level_wrapper_functions(self):
        with patch('skills.incident_forensics_audit_archiver.incident_audit_trail_collector') as mock_collector, \
             patch('skills.incident_forensics_audit_archiver.RecoveryReportExporter') as mock_exporter_cls:

            mock_exporter_instance = mock_exporter_cls.return_value
            mock_collector.collect_incident_audit_trail.return_value = {"status": "ok"}
            mock_exporter_instance.generate_comprehensive_report.return_value = {"report": "done"}
            mock_exporter_instance.finalize_and_export_summary.return_value = "stream_exported"
            mock_exporter_instance.export_epic_report_file.return_value = "file_exported"

            res1 = incident_forensics_audit_archiver.collect_and_report_incident(
                incident_data=self.rand_incident_data,
                destination_path=self.rand_destination,
                include_raw_telemetry=False,
                module_name=self.rand_module_name,
                exception=self.rand_exception,
                traceback_str=self.rand_traceback_str
            )
            self.assertIsNotNone(res1)

            res2 = incident_forensics_audit_archiver.finalize_summary_stream(
                epic_id=self.rand_epic_id,
                stream=self.rand_stream,
                summary_payload=self.rand_summary_payload,
                export_format=self.rand_export_format
            )
            self.assertEqual(res2, "stream_exported")

            res3 = incident_forensics_audit_archiver.export_report_file(
                report_payload=self.rand_report_payload,
                output_path=self.rand_output_path
            )
            self.assertEqual(res3, "file_exported")

if __name__ == '__main__':
    unittest.main()