import unittest
import uuid
import random
import json
import os
import io
import datetime

from skills.incident_aggregator import IncidentAggregator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.incident_post_mortem_reporter import IncidentPostMortemReporter, generate_incident_post_mortem

class TestIncidentPostMortemReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.system_id = str(uuid.uuid4())
        self.severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.severity = random.choice(self.severity_levels)
        self.summary_text = f"Integration test incident summary {random.randint(1000, 9999)}"

        self.aggregator = IncidentAggregator()
        self.trend_analyzer = IncidentTrendAnalyzer()
        self.reporter = IncidentPostMortemReporter(self.aggregator, self.trend_analyzer)

        self.test_output_path = f"test_post_mortem_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.test_output_path):
            try:
                os.remove(self.test_output_path)
            except OSError:
                pass

    def test_integration_generate_and_export_post_mortem(self):
        report = self.reporter.generate(self.incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.incident_id)
        self.assertIn("severity", report)
        self.assertIn("summary", report)
        self.assertIn("trend_score", report)
        self.assertIn("generated_at", report)

        stream = io.BytesIO()
        bytes_written = self.reporter.export_to_stream(self.incident_id, stream)

        self.assertGreater(bytes_written, 0)
        stream.seek(0)
        exported_data = json.loads(stream.read().decode("utf-8"))

        self.assertEqual(exported_data.get("incident_id"), self.incident_id)
        self.assertEqual(exported_data.get("trend_score"), report.get("trend_score"))

    def test_integration_standalone_generator_function(self):
        mock_aggregated_data = {
            "id": self.incident_id,
            "severity": self.severity,
            "summary": self.summary_text
        }
        mock_trend_analysis = {
            "recurrence_score": round(random.uniform(0.0, 1.0), 2)
        }

        result = generate_incident_post_mortem(
            self.system_id,
            mock_aggregated_data,
            mock_trend_analysis,
            self.test_output_path
        )

        self.assertIsInstance(result, dict)
        self.assertIn("report_id", result)
        self.assertEqual(result.get("system_id"), self.system_id)
        self.assertEqual(result.get("aggregated_data"), mock_aggregated_data)
        self.assertEqual(result.get("trend_analysis"), mock_trend_analysis)

        self.assertTrue(os.path.exists(self.test_output_path))

        with open(self.test_output_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content.get("report_id"), result.get("report_id"))
        self.assertEqual(file_content.get("system_id"), self.system_id)
        self.assertEqual(file_content["aggregated_data"]["id"], self.incident_id)
        self.assertEqual(file_content["aggregated_data"]["severity"], self.severity)

if __name__ == "__main__":
    unittest.main()