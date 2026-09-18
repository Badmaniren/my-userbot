import unittest
from unittest.mock import patch
import uuid
import random

from skills.incident_forensics_compliance_checker import (
    IncidentComplianceChecker,
    check_incident_compliance
)


class TestIncidentForensicsComplianceChecker(unittest.TestCase):

    def test_evaluate_compliance_compliant_with_destination(self):
        inc_id = str(uuid.uuid4())
        dest_path = f"/var/log/{uuid.uuid4().hex}.audit"
        risk_score = random.randint(0, 9)
        mock_audit_result = {"status": "collected", "path": dest_path}
        mock_report_result = {"report_id": uuid.uuid4().hex, "status": "generated"}

        with patch("skills.incident_audit_trail_collector.collect_incident_audit_trail", return_value=mock_audit_result) as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as MockBridge:
            
            instance_bridge = MockBridge.return_value
            instance_bridge.generate_comprehensive_report.return_value = mock_report_result

            checker = IncidentComplianceChecker()
            result = checker.evaluate_compliance(
                incident_data={"id": inc_id},
                destination_path=dest_path,
                include_raw_telemetry=True,
                financial_data={"risk_score": risk_score}
            )

            mock_collector.assert_called_once_with(
                incident_data={"id": inc_id},
                destination_path=dest_path,
                include_raw_telemetry=True
            )
            self.assertEqual(result["incident_id"], inc_id)
            self.assertTrue(result["compliant"])
            self.assertEqual(result["compliance_status"], "COMPLIANT")
            self.assertEqual(result["audit_trail"], mock_audit_result)
            self.assertEqual(result["forensics_report"], mock_report_result)
            self.assertEqual(result["risk_assessment"]["score"], risk_score)

    def test_evaluate_compliance_fallback_existing_audit_path(self):
        inc_id = uuid.uuid4().hex
        audit_path = f"/tmp/{uuid.uuid4().hex}.json"
        risk_score = random.randint(10, 100)
        mock_report_result = {"status": "ok", "uuid": uuid.uuid4().hex}

        with patch("skills.incident_audit_trail_collector.collect_incident_audit_trail") as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as MockBridge:
            
            instance_bridge = MockBridge.return_value
            instance_bridge.generate_comprehensive_report.return_value = mock_report_result

            checker = IncidentComplianceChecker()
            result = checker.evaluate_compliance(
                incident_data={"incident_id": inc_id},
                destination_path=None,
                audit_trail_path=audit_path,
                financial_data={"risk_score": risk_score}
            )

            mock_collector.assert_not_called()
            self.assertEqual(result["incident_id"], inc_id)
            self.assertFalse(result["compliant"])
            self.assertEqual(result["compliance_status"], "NON_COMPLIANT")
            self.assertEqual(result["audit_trail"], {"status": "success", "path": audit_path})
            self.assertEqual(result["forensics_report"], mock_report_result)
            self.assertEqual(result["risk_assessment"]["score"], risk_score)

    def test_stream_compliance_package(self):
        inc_id = str(uuid.uuid4())
        format_type = random.choice(["json", "pdf", "xml"])
        expected_stream = iter([uuid.uuid4().bytes, uuid.uuid4().bytes])

        with patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as MockBridge:
            instance_bridge = MockBridge.return_value
            instance_bridge.stream_report_package.return_value = expected_stream

            checker = IncidentComplianceChecker()
            stream = checker.stream_compliance_package(
                incident_id=inc_id,
                financial_data={"impact": random.randint(100, 5000)},
                format_type=format_type
            )

            instance_bridge.stream_report_package.assert_called_once_with(
                incident_id=inc_id,
                financial_data={"impact": random.randint(100, 5000)} if False else {"impact": 500},
                format_type=format_type
            )
            self.assertEqual(stream, expected_stream)

    def test_check_incident_compliance_functional_wrapper(self):
        inc_id = uuid.uuid4().hex
        dest_path = f"/logs/{uuid.uuid4().hex}"
        risk_score = 5

        with patch("skills.incident_audit_trail_collector.collect_incident_audit_trail", return_value={"mocked": True}) as mock_collector, \
             patch("skills.incident_forensics_compliance_checker.IncidentForensicsReportBridge") as MockBridge:
            
            instance_bridge = MockBridge.return_value
            instance_bridge.generate_comprehensive_report.return_value = {"report": "data"}

            result = check_incident_compliance(
                incident_data={"id": inc_id, "module_name": "test_mod"},
                destination_path=dest_path,
                financial_data={"risk_score": risk_score},
                format_type="xml"
            )

            mock_collector.assert_called_once()
            self.assertEqual(result["incident_id"], inc_id)
            self.assertTrue(result["compliant"])
            self.assertEqual(result["risk_assessment"]["score"], risk_score)


if __name__ == "__main__":
    unittest.main()