import unittest
import uuid
import random
import os
import tempfile
from skills.incident_forensics_report_bridge import IncidentForensicsReportBridge
from skills.incident_forensics_synthesizer import IncidentForensicsSynthesizer
from skills.incident_business_loss_reporter import IncidentBusinessLossReporter
from skills.incident_financial_impact_evaluator import IncidentFinancialImpactEvaluator
from skills.incident_impact_analyzer import IncidentImpactAnalyzer

class TestIncidentForensicsReportBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = f"INC-{uuid.uuid4()}"
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.exception_msg = f"Critical error code {random.randint(500, 599)}"
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\n    raise Exception('{self.exception_msg}')"
        
        self.financial_data = {
            "downtime_minutes": random.randint(10, 300),
            "affected_users": random.randint(100, 50000),
            "revenue_loss_per_hour": round(random.uniform(1000.0, 50000.0), 2)
        }
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.json")

        financial_evaluator = IncidentFinancialImpactEvaluator()
        impact_analyzer = IncidentImpactAnalyzer()

        self.forensics_synthesizer = IncidentForensicsSynthesizer()
        self.business_loss_reporter = IncidentBusinessLossReporter(
            financial_evaluator=financial_evaluator,
            impact_analyzer=impact_analyzer
        )
        
        self.bridge = IncidentForensicsReportBridge(
            forensics_synthesizer=self.forensics_synthesizer,
            business_loss_reporter=self.business_loss_reporter
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_comprehensive_bridge_integration(self):
        result = self.bridge.generate_comprehensive_report(
            incident_id=self.incident_id,
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            financial_data=self.financial_data,
            export_path=self.export_path
        )

        self.assertIsNotNone(result)
        self.assertIn("forensics", result)
        self.assertIn("business_loss", result)
        
        self.assertEqual(result["forensics"].get("incident_id"), self.incident_id)
        self.assertEqual(result["business_loss"].get("incident_id"), self.incident_id)

        self.assertTrue(os.path.exists(self.export_path), "Экспортированный файл отчета должен быть создан на диске.")
        
        with open(self.export_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(self.incident_id, file_content)

if __name__ == "__main__":
    unittest.main()