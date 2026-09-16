import unittest
import uuid
import random
import os
import tempfile
from skills.incident_business_loss_reporter import IncidentBusinessLossReporter
from skills.incident_financial_impact_evaluator import IncidentFinancialImpactEvaluator
from skills.incident_impact_analyzer import IncidentImpactAnalyzer

class TestIncidentBusinessLossReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.reporter = IncidentBusinessLossReporter()
        self.financial_evaluator = IncidentFinancialImpactEvaluator()
        self.impact_analyzer = IncidentImpactAnalyzer()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_generate_and_export_business_loss_report(self):
        incident_id = str(uuid.uuid4())
        base_loss = round(random.uniform(1000.0, 500000.0), 2)
        downtime_hours = random.randint(1, 72)
        
        raw_impact_data = {
            "incident_id": incident_id,
            "downtime_hours": downtime_hours,
            "affected_users_count": random.randint(100, 50000),
            "base_hourly_loss": base_loss
        }

        analyzed_impact = self.impact_analyzer.analyze(raw_impact_data)
        financial_assessment = self.financial_evaluator.evaluate(analyzed_impact)

        export_filename = f"report_{incident_id}.json"
        export_path = os.path.join(self.test_dir, export_filename)

        report_result = self.reporter.generate_report(
            incident_id=incident_id,
            financial_data=financial_assessment,
            export_path=export_path
        )

        self.assertEqual(report_result.get("incident_id"), incident_id)
        self.assertIn("total_loss", report_result)
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(incident_id, file_content)

if __name__ == "__main__":
    unittest.main()