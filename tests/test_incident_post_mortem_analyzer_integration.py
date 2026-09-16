import unittest
import uuid
import random
import os
import tempfile
from skills.incident_post_mortem_analyzer import IncidentPostMortemAnalyzer
from skills.incident_aggregator import IncidentAggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.system_health_aggregator import SystemHealthAggregator

class TestIncidentPostMortemAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = IncidentPostMortemAnalyzer()
        self.aggregator = IncidentAggregator()
        self.evaluator = IncidentSeverityEvaluator()
        self.health_aggregator = SystemHealthAggregator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_post_mortem_analysis_pipeline_integration(self):
        incident_id = str(uuid.uuid4())
        component_name = f"service-{random.randint(1000, 9999)}"
        downtime_minutes = random.randint(5, 120)
        error_code = f"ERR_{random.randint(500, 599)}"

        raw_report = (
            f"Incident ID: {incident_id}\n"
            f"Component: {component_name}\n"
            f"Downtime: {downtime_minutes} minutes\n"
            f"Root Cause: Database connection pool exhaustion due to unclosed cursors.\n"
            f"Error Code: {error_code}\n"
            f"Action Items: Implement connection pooling limits and auto-recovery timeout."
        )

        report_filename = f"post_mortem_{incident_id}.txt"
        report_path = os.path.join(self.test_dir, report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(raw_report)

        health_data = self.health_aggregator.aggregate()
        severity_result = self.evaluator.evaluate(error_code=error_code, impact_score=downtime_minutes)
        aggregated_incident = self.aggregator.collect(
            incident_id=incident_id,
            component=component_name,
            severity=severity_result.get("severity", "HIGH")
        )

        analysis_result = self.analyzer.analyze(
            report_path=report_path,
            context={
                "health_status": health_data,
                "severity_data": severity_result,
                "aggregated_incident": aggregated_incident
            }
        )

        self.assertIn("metrics", analysis_result)
        self.assertIn("root_cause", analysis_result)
        self.assertIn("action_items", analysis_result)

        extracted_downtime = analysis_result["metrics"].get("downtime_minutes")
        self.assertEqual(extracted_downtime, downtime_minutes)

        self.assertIn("Database connection pool exhaustion", analysis_result["root_cause"])

        exported_report_path = os.path.join(self.test_dir, f"analyzed_{incident_id}.json")
        export_status = self.analyzer.export_analysis(analysis_result, exported_report_path)

        self.assertTrue(export_status)
        self.assertTrue(os.path.exists(exported_report_path))

        with open(exported_report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(incident_id, content)
            self.assertIn(component_name, content)

if __name__ == "__main__":
    unittest.main()