import unittest
import uuid
import random
import os
import tempfile
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestIncidentTrendAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer = IncidentTrendAnalyzer()
        self.aggregator = IncidentAggregator()
        self.recovery_hub = ErrorRecoveryHub()
        self.dashboard_generator = RecoveryDashboardGenerator()
        
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.random_error_msg = f"Random connection timeout error {random.randint(1000, 9999)}"
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\nException: {self.random_error_msg}"

    def test_trend_analyzer_and_recovery_flow(self):
        try:
            raise RuntimeError(self.random_error_msg)
        except RuntimeError as e:
            captured_incident = self.aggregator.process_and_aggregate(
                module_name=self.module_name,
                exception=e,
                traceback_str=self.traceback_str,
                incident_id=self.incident_id
            )
            
            self.assertIsNotNone(captured_incident)

        history = self.recovery_hub.get_incident_history(self.module_name)
        self.assertIsInstance(history, (list, dict, str))

        trend_result = self.analyzer.analyze_trends(self.module_name)
        self.assertIsNotNone(trend_result)

        health_metrics = self.dashboard_generator.aggregate_system_health()
        dashboard_html = self.dashboard_generator.generate_dashboard(
            metrics=health_metrics,
            incidents=[self.incident_id],
            reports=[str(trend_result)],
            format="html"
        )
        self.assertIsInstance(dashboard_html, str)
        self.assertTrue(len(dashboard_html) > 0)

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, f"dashboard_{uuid.uuid4().hex}.html")
            export_success = self.dashboard_generator.export_dashboard(
                payload={"html": dashboard_html, "id": self.incident_id},
                path=file_path
            )
            
            if export_success is not None:
                self.assertTrue(export_success)
                self.assertTrue(os.path.exists(file_path))
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn(self.incident_id, content)

if __name__ == "__main__":
    unittest.main()