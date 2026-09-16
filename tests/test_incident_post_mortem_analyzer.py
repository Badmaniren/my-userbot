import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.incident_post_mortem_analyzer import IncidentPostMortemAnalyzer


class TestIncidentPostMortemAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = IncidentPostMortemAnalyzer()
        self.random_suffix = uuid.uuid4().hex[:8]
        self.incident_id = f"INC-{random.randint(1000, 9999)}-{self.random_suffix}"
        self.root_cause = f"Root cause: memory leak in subsystem {uuid.uuid4().hex[:6]}"
        self.metric_name = f"metric_downtime_{random.randint(10, 99)}"
        self.metric_value = round(random.uniform(1.5, 99.9), 2)

    def test_extract_metrics_success(self):
        report_content = (
            f"Incident ID: {self.incident_id}\n"
            f"Metric: {self.metric_name} = {self.metric_value} minutes\n"
            f"{self.root_cause}"
        )
        fake_file = io.BytesIO(report_content.encode('utf-8'))

        with patch('skills.incident_post_mortem_analyzer.open', return_value=fake_file, create=True):
            file_path = f"/var/logs/incidents/{uuid.uuid4().hex}.log"
            metrics = self.analyzer.extract_metrics(file_path)

            self.assertIsInstance(metrics, dict)
            self.assertIn(self.metric_name, metrics)
            self.assertEqual(metrics[self.metric_name], self.metric_value)

    def test_find_root_causes_valid_data(self):
        report_lines = [
            f"Timestamp: {random.randint(100000, 999999)}",
            f"Severity: SEV-{random.randint(1, 4)}",
            self.root_cause,
            f"Action: apply patch {uuid.uuid4().hex[:4]}"
        ]
        report_content = "\n".join(report_lines)
        fake_file = io.BytesIO(report_content.encode('utf-8'))

        with patch('skills.incident_post_mortem_analyzer.open', return_value=fake_file, create=True):
            file_path = f"/opt/reports/{uuid.uuid4().hex}.txt"
            causes = self.analyzer.find_root_causes(file_path)

            self.assertIsInstance(causes, list)
            self.assertTrue(any(self.root_cause in cause for cause in causes))

    def test_prevent_recurrence_generates_action(self):
        incident_data = {
            "id": self.incident_id,
            "root_cause": self.root_cause,
            "impact_score": random.randint(1, 10)
        }

        action_plan = self.analyzer.prevent_recurrence(incident_data)

        self.assertIsInstance(action_plan, dict)
        self.assertIn("action_id", action_plan)
        self.assertIn("status", action_plan)
        self.assertEqual(action_plan.get("target_incident"), self.incident_id)

    def test_analyze_full_report_comprehensive(self):
        full_text = (
            f"=== POST MORTEM: {self.incident_id} ===\n"
            f"Description: System failure due to timeout.\n"
            f"Root Cause: {self.root_cause}\n"
            f"Metric::{self.metric_name}::{self.metric_value}\n"
        )
        fake_file = io.BytesIO(full_text.encode('utf-8'))

        with patch('skills.incident_post_mortem_analyzer.open', return_value=fake_file, create=True):
            target_path = f"/home/secops/{uuid.uuid4().hex}.md"
            analysis_result = self.analyzer.analyze_report(target_path)

            self.assertIsInstance(analysis_result, dict)
            self.assertEqual(analysis_result.get("incident_id"), self.incident_id)
            self.assertIn(self.root_cause, analysis_result.get("root_causes", []))
            self.assertEqual(analysis_result.get("metrics", {}).get(self.metric_name), self.metric_value)


if __name__ == '__main__':
    unittest.main()