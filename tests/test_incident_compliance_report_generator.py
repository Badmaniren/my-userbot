import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_compliance_report_generator import start_new


class TestIncidentComplianceReportGenerator(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.audit_trail_id = uuid.uuid4().hex
        self.compliance_standard = f"ISO-{random.randint(20000, 29999)}"
        self.report_format = random.choice(["json", "pdf", "html", "xml"])
        self.output_path = f"/var/reports/{uuid.uuid4().hex}.{self.report_format}"
        
        self.mock_aggregated_data = {
            "incident_id": self.incident_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": "".join(random.choices(string.ascii_letters + " ", k=32)),
            "financial_loss": round(random.uniform(1000.0, 999999.0), 2)
        }
        
        self.mock_audit_tracks = [
            {
                "audit_id": self.audit_trail_id,
                "timestamp": random.randint(1600000000, 1700000000),
                "action": f"ACTION_{uuid.uuid4().hex[:6].upper()}",
                "status": "COMPLIANT"
            }
        ]

    def test_start_new_success_generation(self):
        with patch("skills.incident_compliance_report_generator.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_compliance_report_generator.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_compliance_report_generator.incident_forensics_compliance_checker") as mock_checker:
            
            mock_aggregator.fetch_incident_data.return_value = self.mock_aggregated_data
            mock_collector.collect_tracks.return_value = self.mock_audit_tracks
            
            expected_compliance_result = {
                "status": "APPROVED",
                "standard": self.compliance_standard,
                "checked_items": len(self.mock_audit_tracks)
            }
            mock_checker.verify_compliance.return_value = expected_compliance_result

            result = start_new(
                incident_id=self.incident_id,
                standard=self.compliance_standard,
                report_format=self.report_format
            )

            mock_aggregator.fetch_incident_data.assert_called_once_with(self.incident_id)
            mock_collector.collect_tracks.assert_called_once_with(self.incident_id)
            mock_checker.verify_compliance.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("compliance_status"), "APPROVED")
            self.assertEqual(result.get("standard"), self.compliance_standard)
            self.assertIn("report_id", result)

    def test_start_new_missing_incident_data(self):
        with patch("skills.incident_compliance_report_generator.incident_aggregator") as mock_aggregator:
            mock_aggregator.fetch_incident_data.return_value = None

            with self.assertRaises(ValueError) as ctx:
                start_new(
                    incident_id=self.incident_id,
                    standard=self.compliance_standard,
                    report_format=self.report_format
                )

            self.assertIn(self.incident_id, str(ctx.exception))
            mock_aggregator.fetch_incident_data.assert_called_once_with(self.incident_id)

    def test_start_new_stream_export_handling(self):
        random_bytes_content = "".join(random.choices(string.printable, k=128)).encode('utf-8')
        mock_file_stream = io.BytesIO(random_bytes_content)

        with patch("skills.incident_compliance_report_generator.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_compliance_report_generator.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_compliance_report_generator.recovery_report_exporter") as mock_exporter:

            mock_aggregator.fetch_incident_data.return_value = self.mock_aggregated_data
            mock_collector.collect_tracks.return_value = self.mock_audit_tracks
            mock_exporter.export_stream.return_value = mock_file_stream

            result = start_new(
                incident_id=self.incident_id,
                standard=self.compliance_standard,
                report_format=self.report_format,
                export_to_stream=True
            )

            mock_exporter.export_stream.assert_called_once()
            self.assertIn("stream_data", result)
            
            stream_output = result["stream_data"]
            self.assertEqual(stream_output.read(), random_bytes_content)

    def test_start_new_compliance_failure_escalation(self):
        with patch("skills.incident_compliance_report_generator.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_compliance_report_generator.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_compliance_report_generator.incident_forensics_compliance_checker") as mock_checker, \
             patch("skills.incident_compliance_report_generator.incident_auto_escalation_engine") as mock_escalation:

            mock_aggregator.fetch_incident_data.return_value = self.mock_aggregated_data
            mock_collector.collect_tracks.return_value = self.mock_audit_tracks
            
            failed_compliance_result = {
                "status": "FAILED",
                "standard": self.compliance_standard,
                "violations": [uuid.uuid4().hex, uuid.uuid4().hex]
            }
            mock_checker.verify_compliance.return_value = failed_compliance_result

            result = start_new(
                incident_id=self.incident_id,
                standard=self.compliance_standard,
                report_format=self.report_format
            )

            mock_escalation.trigger_escalation.assert_called_once()
            self.assertEqual(result.get("compliance_status"), "FAILED")
            self.assertEqual(len(result.get("violations")), 2)


if __name__ == "__main__":
    unittest.main()