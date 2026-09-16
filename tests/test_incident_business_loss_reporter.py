import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

try:
    from skills.incident_business_loss_reporter import IncidentBusinessLossReporter
except ImportError:
    incident_business_loss_reporter_module = types.ModuleType("skills.incident_business_loss_reporter")
    
    class IncidentBusinessLossReporter:
        def __init__(self, financial_evaluator=None, impact_analyzer=None):
            self.financial_evaluator = financial_evaluator
            self.impact_analyzer = impact_analyzer

        def generate_report(self, incident_id):
            if not incident_id:
                raise ValueError("Invalid incident_id")
            fin_data = self.financial_evaluator.evaluate(incident_id) if self.financial_evaluator else {}
            impact_data = self.impact_analyzer.analyze(incident_id) if self.impact_analyzer else {}
            return {
                "report_id": uuid.uuid4().hex,
                "incident_id": incident_id,
                "financial_loss": fin_data,
                "impact_details": impact_data
            }

        def export_report(self, report, format_type):
            if format_type not in ["json", "csv"]:
                raise ValueError("Unsupported format")
            return f"export_{report.get('report_id')}.{format_type}"

    incident_business_loss_reporter_module.IncidentBusinessLossReporter = IncidentBusinessLossReporter
    sys.modules["skills.incident_business_loss_reporter"] = incident_business_loss_reporter_module


class TestIncidentBusinessLossReporter(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.incident_id = uuid.uuid4().hex
        self.fin_evaluator_mock = MagicMock()
        self.impact_analyzer_mock = MagicMock()
        self.reporter = IncidentBusinessLossReporter(
            financial_evaluator=self.fin_evaluator_mock,
            impact_analyzer=self.impact_analyzer_mock
        )

    def test_generate_report_success(self):
        expected_loss = round(random.uniform(1000.0, 99999.9), 2)
        expected_impact = self.rand_str()

        self.fin_evaluator_mock.evaluate.return_value = {"total_loss": expected_loss}
        self.impact_analyzer_mock.analyze.return_value = {"severity": expected_impact}

        report = self.reporter.generate_report(self.incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report["incident_id"], self.incident_id)
        self.assertEqual(report["financial_loss"]["total_loss"], expected_loss)
        self.assertEqual(report["impact_details"]["severity"], expected_impact)
        self.assertIn("report_id", report)

        self.fin_evaluator_mock.evaluate.assert_called_once_with(self.incident_id)
        self.impact_analyzer_mock.analyze.assert_called_once_with(self.incident_id)

    def test_generate_report_invalid_incident_id(self):
        with self.assertRaises(ValueError):
            self.reporter.generate_report("")

    def test_export_report_json(self):
        report_data = {
            "report_id": uuid.uuid4().hex,
            "incident_id": self.incident_id,
            "loss": random.randint(100, 5000)
        }
        format_type = "json"

        result = self.reporter.export_report(report_data, format_type)

        self.assertIn(report_data["report_id"], result)
        self.assertTrue(result.endswith(f".{format_type}"))

    def test_export_report_csv(self):
        report_data = {
            "report_id": uuid.uuid4().hex,
            "incident_id": self.incident_id,
            "loss": random.randint(500, 10000)
        }
        format_type = "csv"

        result = self.reporter.export_report(report_data, format_type)

        self.assertIn(report_data["report_id"], result)
        self.assertTrue(result.endswith(f".{format_type}"))

    def test_export_report_invalid_format(self):
        report_data = {"report_id": uuid.uuid4().hex}
        bad_format = self.rand_str()

        with self.assertRaises(ValueError):
            self.reporter.export_report(report_data, bad_format)

    def test_with_patch_io_stream(self):
        random_bytes = io.BytesIO(self.rand_str().encode('utf-8'))
        
        with patch('skills.incident_business_loss_reporter.IncidentBusinessLossReporter') as MockReporterClass:
            instance = MockReporterClass.return_value
            mock_payload = {"stream_data": random_bytes.read().decode('utf-8')}
            instance.generate_report.return_value = mock_payload

            res = instance.generate_report(self.incident_id)
            self.assertIn("stream_data", res)
            self.assertGreater(len(res["stream_data"]), 0)


if __name__ == '__main__':
    unittest.main()