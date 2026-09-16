import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json
from skills.incident_business_loss_reporter import IncidentBusinessLossReporter, incident_business_loss_reporter

class TestIncidentBusinessLossReporter(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.currency = random.choice(["USD", "EUR", "GBP", "JPY", "RUB"])
        self.total_loss = round(random.uniform(100.0, 99999.9), 2)
        self.direct_loss = round(self.total_loss * 0.7, 2)
        self.indirect_loss = round(self.total_loss * 0.3, 2)

        self.downtime = random.randint(10, 500)
        self.services_count = random.randint(1, 15)
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        self.mock_fin_eval = MagicMock()
        self.mock_fin_eval.evaluate.return_value = {
            "report_id": str(uuid.uuid4()),
            "currency": self.currency,
            "total_loss": self.total_loss,
            "direct_financial_loss": self.direct_loss,
            "indirect_financial_loss": self.indirect_loss,
            "details": str(uuid.uuid4())
        }

        self.mock_impact_analyzer = MagicMock()
        self.mock_impact_analyzer.analyze.return_value = {
            "downtime_minutes": self.downtime,
            "affected_services_count": self.services_count,
            "severity_level": self.severity
        }

        self.reporter = IncidentBusinessLossReporter(
            financial_evaluator=self.mock_fin_eval,
            impact_analyzer=self.mock_impact_analyzer
        )

    def test_init_defaults(self):
        with patch('skills.incident_business_loss_reporter.incident_financial_impact_evaluator') as mock_fe, \
             patch('skills.incident_business_loss_reporter.incident_impact_analyzer') as mock_ia:
            reporter = IncidentBusinessLossReporter()
            self.assertIsNotNone(reporter.financial_evaluator)
            self.assertIsNotNone(reporter.impact_analyzer)
            mock_fe.assert_called_once()
            mock_ia.assert_called_once()

    def test_factory_function(self):
        rep = incident_business_loss_reporter()
        self.assertIsInstance(rep, IncidentBusinessLossReporter)

    def test_generate_report_basic(self):
        report = self.reporter.generate_report(self.incident_id)

        self.mock_fin_eval.evaluate.assert_called_once_with(self.incident_id)
        self.mock_impact_analyzer.analyze.assert_called_once_with(self.incident_id)

        self.assertEqual(report["incident_id"], self.incident_id)
        self.assertEqual(report["currency"], self.currency)
        self.assertEqual(report["total_loss"], self.total_loss)
        self.assertTrue(report["is_generated"])

        self.assertEqual(report["financial_metrics"]["total_loss"], self.total_loss)
        self.assertEqual(report["financial_metrics"]["direct_financial_loss"], self.direct_loss)
        self.assertEqual(report["financial_metrics"]["indirect_financial_loss"], self.indirect_loss)

        self.assertEqual(report["impact_metrics"]["downtime_minutes"], self.downtime)
        self.assertEqual(report["impact_metrics"]["affected_services_count"], self.services_count)
        self.assertEqual(report["impact_metrics"]["severity_level"], self.severity)

    def test_generate_report_with_overrides(self):
        override_fin = {
            "report_id": str(uuid.uuid4()),
            "currency": "CAD",
            "total_loss": 5555.55,
            "direct_financial_loss": 4000.00,
            "indirect_financial_loss": 1555.55
        }
        override_impact = {
            "downtime_minutes": 99,
            "affected_services_count": 3,
            "severity_level": "LOW"
        }

        report = self.reporter.generate_report(
            self.incident_id,
            financial_impact=override_fin,
            impact_analysis=override_impact
        )

        self.mock_fin_eval.evaluate.assert_not_called()
        self.mock_impact_analyzer.analyze.assert_not_called()

        self.assertEqual(report["currency"], "CAD")
        self.assertEqual(report["total_loss"], 5555.55)
        self.assertEqual(report["impact_metrics"]["downtime_minutes"], 99)
        self.assertEqual(report["impact_metrics"]["severity_level"], "LOW")

    def test_generate_report_with_export(self):
        export_file_path = f"{uuid.uuid4()}.json"
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("json.dump") as mock_json_dump:

            report = self.reporter.generate_report(self.incident_id, export_path=export_file_path)

            mock_file.assert_called_once_with(export_file_path, 'w', encoding='utf-8')
            mock_json_dump.assert_called_once()
            self.assertEqual(report["export_status"], "success")

    def test_aggregate_losses(self):
        key = str(uuid.uuid4())
        val1 = round(random.uniform(1.0, 100.0), 2)
        val2 = round(random.uniform(1.0, 100.0), 2)
        sub_data = [{key: val1}, {key: val2}]

        total = self.reporter._aggregate_losses(sub_data, key=key)
        self.assertAlmostEqual(total, val1 + val2)

    def test_aggregate_losses_default_key(self):
        val1 = round(random.uniform(1.0, 50.0), 2)
        val2 = round(random.uniform(1.0, 50.0), 2)
        sub_data = [{"loss": val1}, {"loss": val2}]

        total = self.reporter._aggregate_losses(sub_data)
        self.assertAlmostEqual(total, val1 + val2)

    def test_generate_stream_report(self):
        stream = self.reporter.generate_stream_report(self.incident_id)
        self.assertIsInstance(stream, io.BytesIO)

        content = stream.getvalue()
        parsed_data = json.loads(content.decode('utf-8'))

        self.assertEqual(parsed_data["incident_id"], self.incident_id)
        self.assertEqual(parsed_data["total_loss"], self.total_loss)
        self.assertTrue(parsed_data["is_generated"])

if __name__ == '__main__':
    unittest.main()