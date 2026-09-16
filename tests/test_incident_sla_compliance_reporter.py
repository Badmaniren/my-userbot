import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from datetime import datetime

from skills.incident_sla_compliance_reporter import (
    IncidentSlaComplianceReporter,
    ComplianceReportError,
    incident_sla_compliance_reporter
)

class TestIncidentSlaComplianceReporter(unittest.TestCase):

    def setUp(self):
        self.reporter_id = uuid.uuid4().hex
        self.standard = f"ISO-{random.randint(2000, 9999)}"
        self.reporter = IncidentSlaComplianceReporter(reporter_id=self.reporter_id, standard=self.standard)

    def test_generate_audit_report_success(self):
        metric_id = uuid.uuid4().hex
        tracker_metrics = {"metric_id": metric_id, "value": random.random()}
        breach_predictors = {"risk": random.choice(["high", "low"])}
        mitigation_plans = [uuid.uuid4().hex, uuid.uuid4().hex]

        report = self.reporter.generate_audit_report(
            tracker_metrics=tracker_metrics,
            breach_predictors=breach_predictors,
            mitigation_plans=mitigation_plans
        )

        self.assertEqual(report["reporter_id"], self.reporter_id)
        self.assertEqual(report["standard"], self.standard)
        self.assertEqual(report["metrics"], tracker_metrics)
        self.assertEqual(report["predictors"], breach_predictors)
        self.assertEqual(report["mitigation_plans"], mitigation_plans)
        self.assertIn("generated_at", report)

    def test_generate_audit_report_invalid_metrics_raises_error(self):
        invalid_metrics = {"invalid_key": uuid.uuid4().hex}
        breach_predictors = {}
        mitigation_plans = []

        with self.assertRaises(ComplianceReportError):
            self.reporter.generate_audit_report(
                tracker_metrics=invalid_metrics,
                breach_predictors=breach_predictors,
                mitigation_plans=mitigation_plans
            )

    def test_generate_audit_report_non_list_mitigation_plan(self):
        metric_id = uuid.uuid4().hex
        tracker_metrics = {"metric_id": metric_id}
        breach_predictors = {}
        single_plan = uuid.uuid4().hex

        report = self.reporter.generate_audit_report(
            tracker_metrics=tracker_metrics,
            breach_predictors=breach_predictors,
            mitigation_plans=single_plan
        )

        self.assertEqual(report["mitigation_plans"], [single_plan])

    def test_create_compliance_status_log(self):
        log_prefix = uuid.uuid4().hex
        audit_passed = random.choice([True, False])
        score = random.randint(0, 100)
        compliance_data = {
            "log_prefix": log_prefix,
            "audit_passed": audit_passed,
            "score": score
        }

        log_str = self.reporter.create_compliance_status_log(compliance_data)

        self.assertIn(log_prefix, log_str)
        self.assertIn(self.standard, log_str)
        self.assertIn(str(audit_passed), log_str)
        self.assertIn(str(score), log_str)

    def test_export_report_stream(self):
        report = {
            "id": uuid.uuid4().hex,
            "val": random.randint(1, 100)
        }
        stream = io.BytesIO()
        self.reporter.export_report_stream(report, stream)

        stream.seek(0)
        content = stream.read()
        parsed = json.loads(content.decode('utf-8'))
        self.assertEqual(parsed, report)

    def test_submit_report_governance(self):
        endpoint = f"https://{uuid.uuid4().hex}.gov/api/v1/submit"
        payload = {"data_id": uuid.uuid4().hex}
        mock_response_data = {"status": "accepted", "ref": uuid.uuid4().hex}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = self.reporter.submit_report_governance(endpoint, payload)

            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(result, mock_response_data)

    def test_submit_report_to_governance_alias(self):
        endpoint = f"https://{uuid.uuid4().hex}.gov/api/v1/submit"
        payload = {"data_id": uuid.uuid4().hex}
        mock_response_data = {"status": "ok"}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = self.reporter.submit_report_to_governance(endpoint, payload)

            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(result, mock_response_data)

    def test_incident_sla_compliance_reporter_function_flow(self):
        incident_id = uuid.uuid4().hex
        metric_id = uuid.uuid4().hex
        tracker_metrics = {"metric_id": metric_id, "score": random.randint(50, 100)}
        breach_predictors = {"probability": random.random()}
        mitigation_plans = [uuid.uuid4().hex]

        expected_filename = f"audit_report_{incident_id}.log"

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            result = incident_sla_compliance_reporter(
                incident_id=incident_id,
                tracker_metrics=tracker_metrics,
                breach_predictors=breach_predictors,
                mitigation_plans=mitigation_plans
            )

            mock_file.assert_called_once_with(expected_filename, "w")
            handle = mock_file()
            handle.write.assert_any_call(f"Incident ID: {incident_id}\n")
            self.assertEqual(result["reporter_id"], incident_id)
            self.assertEqual(result["metrics"], tracker_metrics)