import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_sla_audit_reporter import IncidentSLAAuditReporter


class TestIncidentSLAAuditReporter(unittest.TestCase):

    def setUp(self):
        self.tracker_mock = MagicMock()
        self.predictor_mock = MagicMock()
        self.reporter = IncidentSLAAuditReporter(
            sla_tracker=self.tracker_mock,
            sla_predictor=self.predictor_mock
        )

    def test_generate_audit_report_success(self):
        random_id_1 = uuid.uuid4().hex
        random_id_2 = uuid.uuid4().hex
        random_name_1 = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_name_2 = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_compliance = round(random.uniform(85.0, 99.9), 2)
        random_risk_score = round(random.uniform(0.01, 0.50), 4)

        self.tracker_mock.get_metrics.return_value = {
            "audit_period": random_id_1,
            "monitored_services": [random_name_1, random_name_2],
            "overall_compliance": random_compliance,
            "breached_incidents": 0
        }

        self.predictor_mock.evaluate_risks.return_value = {
            "prediction_id": random_id_2,
            "risk_score": random_risk_score,
            "vulnerable_services": [random_name_1]
        }

        report = self.reporter.generate_audit_report(period_id=random_id_1)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("period_id"), random_id_1)
        self.assertEqual(report.get("compliance_rate"), random_compliance)
        self.assertEqual(report.get("predicted_risk"), random_risk_score)
        self.assertIn(random_name_1, report.get("vulnerabilities", []))

        self.tracker_mock.get_metrics.assert_called_once_with(period_id=random_id_1)
        self.predictor_mock.evaluate_risks.assert_called_once()

    def test_export_report_to_stream(self):
        random_report_key = uuid.uuid4().hex
        random_value = ''.join(random.choices(string.ascii_letters, k=15))

        mock_report_data = {
            random_report_key: random_value,
            "timestamp": random.randint(1000000000, 2000000000)
        }

        with patch.object(self.reporter, 'generate_audit_report', return_value=mock_report_data):
            random_stream_name = f"report_{uuid.uuid4().hex}.json"

            with patch('skills.incident_sla_audit_reporter.open', unittest.mock.mock_open()) as mock_file:
                result_path = self.reporter.export_report(
                    target_path=random_stream_name,
                    format_type="json"
                )

                self.assertEqual(result_path, random_stream_name)
                mock_file.assert_called_once_with(random_stream_name, 'w', encoding='utf-8')

                handle = mock_file()
                written_data = "".join(call.args[0] for call in handle.write.call_args_list)
                parsed_data = json.loads(written_data)

                self.assertEqual(parsed_data.get(random_report_key), random_value)

    def test_audit_report_handles_missing_data(self):
        random_bad_id = uuid.uuid4().hex

        self.tracker_mock.get_metrics.side_effect = KeyError(f"Period {random_bad_id} not found")

        with self.assertRaises(KeyError):
            self.reporter.generate_audit_report(period_id=random_bad_id)


if __name__ == '__main__':
    unittest.main()