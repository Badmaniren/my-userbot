import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.incident_forensics_compliance_checker import (
    IncidentComplianceChecker,
    check_incident_compliance
)


class TestIncidentForensicsComplianceChecker(unittest.TestCase):

    def setUp(self):
        self.checker = IncidentComplianceChecker()
        self.random_id = str(uuid.uuid4())
        self.random_dest_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.random_export_path = f"/reports/{uuid.uuid4().hex}.json"
        self.random_module = f"mod_{uuid.uuid4().hex[:8]}"
        self.random_exception = f"Exc_{uuid.uuid4().hex[:6]}"

    def test_evaluate_compliance_compliant_flow(self):
        low_risk_score = random.randint(0, 9)
        financial_data = {
            "risk_score": low_risk_score,
            "loss_amount": round(random.uniform(10.0, 500.0), 2)
        }
        incident_data = {
            "id": self.random_id,
            "module_name": self.random_module,
            "exception": self.random_exception,
            "traceback_str": "Traceback (most recent call last): ..."
        }

        mock_audit_result = {
            "status": "collected",
            "path": self.random_dest_path,
            "items_count": random.randint(1, 100)
        }
        mock_report_result = {
            "report_id": uuid.uuid4().hex,
            "status": "generated"
        }

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector.collect_incident_audit_trail", return_value=mock_audit_result) as mock_collect, \
             patch.object(self.checker.bridge, "generate_comprehensive_report", return_value=mock_report_result) as mock_generate:

            result = self.checker.evaluate_compliance(
                incident_data=incident_data,
                destination_path=self.random_dest_path,
                include_raw_telemetry=True,
                financial_data=financial_data,
                export_path=self.random_export_path,
                format_type="json"
            )

            mock_collect.assert_called_once_with(
                incident_data=incident_data,
                destination_path=self.random_dest_path,
                include_raw_telemetry=True
            )

            mock_generate.assert_called_once_with(
                incident_id=self.random_id,
                financial_data=financial_data,
                export_path=self.random_export_path,
                format_type="json",
                module_name=self.random_module,
                exception=self.random_exception,
                traceback_str="Traceback (most recent call last): ..."
            )

            self.assertEqual(result["incident_id"], self.random_id)
            self.assertTrue(result["compliant"])
            self.assertEqual(result["compliance_status"], "COMPLIANT")
            self.assertEqual(result["audit_trail"], mock_audit_result)
            self.assertEqual(result["forensics_report"], mock_report_result)
            self.assertEqual(result["risk_assessment"]["score"], low_risk_score)

    def test_evaluate_compliance_non_compliant_flow(self):
        high_risk_score = random.randint(10, 100)
        financial_data = {
            "risk_score": high_risk_score,
            "loss_amount": round(random.uniform(1000.0, 50000.0), 2)
        }
        incident_data = {
            "incident_id": self.random_id,
            "module_name": self.random_module
        }

        mock_audit_result = {
            "status": "success",
            "path": self.random_dest_path
        }
        mock_report_result = {
            "report_id": uuid.uuid4().hex,
            "status": "exported"
        }

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector.collect_incident_audit_trail", return_value=mock_audit_result), \
             patch.object(self.checker.bridge, "generate_comprehensive_report", return_value=mock_report_result):

            result = self.checker.evaluate_compliance(
                incident_data=incident_data,
                audit_trail_path=self.random_dest_path,
                financial_data=financial_data,
                format_type="csv"
            )

            self.assertEqual(result["incident_id"], self.random_id)
            self.assertFalse(result["compliant"])
            self.assertEqual(result["compliance_status"], "NON_COMPLIANT")
            self.assertEqual(result["risk_assessment"]["score"], high_risk_score)

    def test_evaluate_compliance_fallback_existing_audit_path(self):
        financial_data = {"risk_score": random.randint(0, 5)}
        mock_report_result = {"status": "ok"}

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector.collect_incident_audit_trail") as mock_collect, \
             patch.object(self.checker.bridge, "generate_comprehensive_report", return_value=mock_report_result):

            result = self.checker.evaluate_compliance(
                incident_id=self.random_id,
                audit_trail_path=self.random_dest_path,
                financial_data=financial_data
            )

            mock_collect.assert_not_called()
            self.assertEqual(result["audit_trail"], {"status": "success", "path": self.random_dest_path})
            self.assertEqual(result["incident_id"], self.random_id)

    def test_evaluate_compliance_unknown_incident_id(self):
        financial_data = {"risk_score": random.randint(0, 15)}
        mock_report_result = {"status": "processed"}

        with patch("skills.incident_forensics_compliance_checker.incident_audit_trail_collector.collect_incident_audit_trail", return_value={}), \
             patch.object(self.checker.bridge, "generate_comprehensive_report", return_value=mock_report_result) as mock_generate:

            result = self.checker.evaluate_compliance(
                incident_data={},
                financial_data=financial_data
            )

            self.assertEqual(result["incident_id"], "unknown")
            args, kwargs = mock_generate.call_args
            self.assertEqual(kwargs["incident_id"], "unknown")

    def test_stream_compliance_package(self):
        format_type = random.choice(["json", "xml", "csv"])
        financial_data = {"risk_score": random.randint(0, 50)}
        expected_stream = iter([uuid.uuid4().hex.encode('utf-8'), uuid.uuid4().hex.encode('utf-8')])

        with patch.object(self.checker.bridge, "stream_report_package", return_value=expected_stream) as mock_stream:
            stream_res = self.checker.stream_compliance_package(
                incident_id=self.random_id,
                financial_data=financial_data,
                format_type=format_type
            )

            mock_stream.assert_called_once_with(
                incident_id=self.random_id,
                financial_data=financial_data,
                format_type=format_type
            )
            self.assertEqual(stream_res, expected_stream)

    def test_check_incident_compliance_wrapper(self):
        financial_data = {"risk_score": random.randint(0, 9)}
        incident_data = {"id": self.random_id}
        mock_response = {
            "incident_id": self.random_id,
            "compliant": True,
            "compliance_status": "COMPLIANT",
            "audit_trail": {},
            "forensics_report": {},
            "risk_assessment": {"score": financial_data["risk_score"]}
        }

        with patch.object(IncidentComplianceChecker, "evaluate_compliance", return_value=mock_response) as mock_eval:
            res = check_incident_compliance(
                incident_data=incident_data,
                destination_path=self.random_dest_path,
                financial_data=financial_data,
                format_type="json"
            )

            mock_eval.assert_called_once_with(
                incident_data=incident_data,
                destination_path=self.random_dest_path,
                include_raw_telemetry=False,
                financial_data=financial_data,
                export_path=None,
                format_type="json",
                incident_id=None,
                audit_trail_path=None
            )
            self.assertEqual(res, mock_response)


if __name__ == "__main__":
    unittest.main()