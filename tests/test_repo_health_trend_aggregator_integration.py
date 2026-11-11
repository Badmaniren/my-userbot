import json
import os
import random
import tempfile
import unittest
import uuid

from skills.repo_health_trend_aggregator import RepoHealthTrendAggregator
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker


class TestRepoHealthTrendAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = RepoHealthTrendAggregator()
        self.tracker = RepoHealthIncidentTracker()

    def test_aggregate_integration_flow(self):
        repo_id = f"repo-{uuid.uuid4().hex}"
        metric_id_1 = f"metric-1-{uuid.uuid4().hex}"
        metric_id_2 = f"metric-2-{uuid.uuid4().hex}"
        val1 = random.randint(1, 100)
        val2 = random.randint(101, 200)

        with tempfile.TemporaryDirectory() as temp_dir:
            file1_path = os.path.join(temp_dir, "metrics_cpu.json")
            file2_path = os.path.join(temp_dir, "metrics_memory.json")

            with open(file1_path, "w", encoding="utf-8") as f:
                json.dump({"metric_id": metric_id_1, "value": val1}, f)

            with open(file2_path, "w", encoding="utf-8") as f:
                json.dump({"metric_id": metric_id_2, "value": val2}, f)

            result = self.aggregator.aggregate(repo_id, temp_dir)

            summary_file = os.path.join(temp_dir, "trend_summary.json")
            self.assertTrue(os.path.exists(summary_file))

            with open(summary_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(saved_data["repo_id"], repo_id)
            self.assertIn(metric_id_1, result["processed_metrics"])
            self.assertIn(metric_id_2, result["processed_metrics"])
            self.assertEqual(saved_data, result)
            self.assertIsInstance(result["associated_incidents"], list)

    def test_aggregate_time_series_calculation(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        val1 = random.uniform(1.0, 10.0)
        val2 = random.uniform(10.0, 20.0)
        val3 = random.uniform(20.0, 30.0)

        time_series = [
            {"metric_name": metric_name, "value": val1},
            {"metric_name": metric_name, "value": val2},
            {"metric_name": metric_name, "value": val3},
            {"metric_name": metric_name, "value": "invalid_string"},
        ]

        summary = self.aggregator.aggregate_time_series(time_series)
        self.assertIn(metric_name, summary)
        metric_stats = summary[metric_name]
        self.assertEqual(metric_stats["count"], 3)
        self.assertAlmostEqual(metric_stats["min"], min(val1, val2, val3))
        self.assertAlmostEqual(metric_stats["max"], max(val1, val2, val3))
        self.assertAlmostEqual(metric_stats["mean"], (val1 + val2 + val3) / 3.0)

    def test_export_prepared_dataset(self):
        random_key = f"key_{uuid.uuid4().hex}"
        random_value = f"val_{uuid.uuid4().hex}"
        dataset = {random_key: random_value}

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, f"export_{uuid.uuid4().hex}.json")
            success = self.aggregator.export_prepared_dataset(dataset, file_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(file_path))

            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded, dataset)

    def test_parse_html_health_report(self):
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        title_text = f"Incident Title {uuid.uuid4().hex[:8]}"
        html_content = (
            f'<div class="incident-item" id="{inc_id}">'
            f'<span class="title">{title_text}</span></div>'
        )

        incidents = self.aggregator.parse_html_health_report(html_content)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["id"], inc_id)
        self.assertEqual(incidents[0]["title"], title_text)


if __name__ == "__main__":
    unittest.main()