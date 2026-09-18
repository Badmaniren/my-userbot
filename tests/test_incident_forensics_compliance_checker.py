import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.incident_forensics_compliance_checker import (
    check_incident_compliance,
    IncidentComplianceChecker
)


class TestIncidentForensicsComplianceChecker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.destination_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Error_{uuid.uuid4().hex[:6]}"
        self.traceback_str = f"Traceback at line {random.randint(1, 1000)}"
        self.export_path = f"/var/reports/{uuid.uuid4().hex}.pdf"
        self.format_type = random.choice(["pdf", "json", "xml", "csv"])

        self.financial_data = {
            "loss_amount": round(random.uniform(100.0, 99999.99), 2),
            "currency": random.choice(["USD", "EUR", "RUB"]),
            "risk_score": random.randint(1, 10)
        }
        self.incident_data = {
            "id": self.incident_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Incident description {uuid.uuid4().hex}"
        }

    def test_collect_incident_audit_trail_called(self):
        random_telemetry = random.choice([True, False])
        mock_audit_result = {
            "audit_trail_id": uuid.uuid4().hex,
            "status": "collected",
            "telemetry_included": random_telemetry
        }

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as mock_bridge_cls:
            
            mock_collector.collect_incident_audit_trail.return_value = mock_audit_result
            mock_bridge_instance = mock_bridge_cls.return_value
            mock_bridge_instance.generate_comprehensive_report.return_value = {
                "report_id": uuid.uuid4().hex,
                "status": "generated"
            }

            result = check_incident_compliance(
                incident_data=self.incident_data,
                destination_path=self.destination_path,
                include_raw_telemetry=random_telemetry,
                financial_data=self.financial_data,
                export_path=self.export_path,
                format_type=self.format_type
            )

            mock_collector.collect_incident_audit_trail.assert_called_once_with(
                incident_data=self.incident_data,
                destination_path=self.destination_path,
                include_raw_telemetry=random_telemetry
            )
            self.assertIn("audit_trail", result)
            self.assertEqual(result["audit_trail"], mock_audit_result)

    def test_incident_forensics_report_bridge_called(self):
        mock_audit_result = {"status": "ok", "path": self.destination_path}
        mock_report_result = {
            "comprehensive_report_id": uuid.uuid4().hex,
            "exported_to": self.export_path,
            "format": self.format_type
        }

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as mock_bridge_cls:
            
            mock_collector.collect_incident_audit_trail.return_value = mock_audit_result
            mock_bridge_instance = mock_bridge_cls.return_value
            mock_bridge_instance.generate_comprehensive_report.return_value = mock_report_result

            checker = IncidentComplianceChecker()
            result = checker.evaluate_compliance(
                incident_data=self.incident_data,
                destination_path=self.destination_path,
                include_raw_telemetry=True,
                financial_data=self.financial_data,
                export_path=self.export_path,
                format_type=self.format_type
            )

            mock_bridge_instance.generate_comprehensive_report.assert_called_once()
            _, kwargs = mock_bridge_instance.generate_comprehensive_report.call_args
            self.assertEqual(kwargs.get("incident_id") or mock_bridge_instance.generate_comprehensive_report.call_args[0][0], self.incident_id)
            self.assertEqual(result["forensics_report"], mock_report_result)

    def test_compliance_status_evaluation_logic(self):
        risk_threshold = random.randint(3, 8)
        self.financial_data["risk_score"] = risk_threshold - 1 if risk_threshold > 1 else 1

        mock_audit_result = {"trail_status": "verified"}
        mock_report_result = {"summary": "clean"}

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as mock_bridge_cls:

            mock_collector.collect_incident_audit_trail.return_value = mock_audit_result
            mock_bridge_instance = mock_bridge_cls.return_value
            mock_bridge_instance.generate_comprehensive_report.return_value = mock_report_result

            result = check_incident_compliance(
                incident_data=self.incident_data,
                destination_path=self.destination_path,
                include_raw_telemetry=False,
                financial_data=self.financial_data,
                export_path=self.export_path,
                format_type=self.format_type
            )

            self.assertTrue(result["compliant"])
            self.assertEqual(result["risk_assessment"]["score"], self.financial_data["risk_score"])

    def test_stream_report_package_integration(self):
        stream_data = f"stream_chunk_{uuid.uuid4().hex}".encode('utf-8')
        
        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as mock_bridge_cls:

            mock_collector.collect_incident_audit_trail.return_value = {"status": "success"}
            mock_bridge_instance = mock_bridge_cls.return_value
            mock_bridge_instance.stream_report_package.return_value = io.BytesIO(stream_data)

            checker = IncidentComplianceChecker()
            stream_res = checker.stream_compliance_package(
                incident_id=self.incident_id,
                financial_data=self.financial_data,
                format_type=self.format_type
            )

            mock_bridge_instance.stream_report_package.assert_called_once_with(
                incident_id=self.incident_id,
                financial_data=self.financial_data,
                format_type=self.format_type
            )
            self.assertEqual(stream_res.read(), stream_data)

    def test_compliance_failure_on_high_risk(self):
        self.financial_data["risk_score"] = 10  # Максимальный риск

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector") as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as mock_bridge_cls:

            mock_collector.collect_incident_audit_trail.return_value = {"status": "failed"}
            mock_bridge_instance = mock_bridge_cls.return_value
            mock_bridge_instance.generate_comprehensive_report.return_value = {"status": "error"}

            result = check_incident_compliance(
                incident_data=self.incident_data,
                destination_path=self.destination_path,
                include_raw_telemetry=True,
                financial_data=self.financial_data,
                export_path=self.export_path,
                format_type=self.format_type
            )

            self.assertFalse(result["compliant"])
            self.assertEqual(result["risk_assessment"]["score"], 10)


if __name__ == "__main__":
    unittest.main()