import unittest
import uuid
import random
import io
from skills.incident_post_mortem_analyzer import IncidentPostMortemAnalyzer
from skills.incident_aggregator import IncidentAggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer

class IntegrationTestIncidentPostMortemAnalyzer(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.severity_evaluator = IncidentSeverityEvaluator()
        self.trend_analyzer = IncidentTrendAnalyzer()
        self.analyzer = IncidentPostMortemAnalyzer(
            aggregator=self.aggregator,
            severity_evaluator=self.severity_evaluator,
            trend_analyzer=self.trend_analyzer
        )

    def test_integration_analyze_incident_flow(self):
        random_suffix = random.randint(1000, 9999)
        incident_id = f"inc-{uuid.uuid4()}-{random_suffix}"

        result = self.analyzer.analyze_incident(incident_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_id"], incident_id)
        self.assertEqual(result["status"], "analyzed")
        self.assertIn("post_mortem_id", result)
        self.assertTrue(uuid.UUID(result["post_mortem_id"]))

    def test_integration_analyze_with_telemetry_and_severity(self):
        random_suffix = random.randint(100, 999)
        incident_id = f"target-{uuid.uuid4()}-{random_suffix}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        telemetry_data = {
            "cpu_usage": random.randint(50, 100),
            "memory_leak": bool(random.getrandbits(1)),
            "error_code": f"ERR_SYS_{random.randint(1, 500)}"
        }

        severity_info = {"severity": chosen_severity}

        result = self.analyzer.analyze(
            incident_id=incident_id,
            telemetry=telemetry_data,
            severity_info=severity_info
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["target_incident_id"], incident_id)
        self.assertEqual(result["severity"], chosen_severity)
        self.assertEqual(result["status"], "analyzed")
        self.assertIn(str(telemetry_data["cpu_usage"]), result["root_cause_analysis"])

    def test_integration_generate_report_with_stream(self):
        random_suffix = random.randint(10000, 99999)
        incident_id = f"rep-{uuid.uuid4()}-{random_suffix}"
        expected_content = f"Log stream payload data {random.random()}"

        stream = io.BytesIO(expected_content.encode('utf-8'))

        incident_data = {
            "incident_id": incident_id,
            "stream": stream
        }

        report = self.analyzer.generate_report(incident_data)

        self.assertIsInstance(report, str)
        self.assertIn(incident_id, report)
        self.assertIn(expected_content, report)

if __name__ == "__main__":
    unittest.main()