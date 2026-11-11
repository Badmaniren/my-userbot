import unittest
import unittest.mock
import json
import os
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.repo_health_trend_aggregator import RepoHealthTrendAggregator

class TestRepoHealthTrendAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthTrendAggregator()

    def test_aggregate_time_series_logic(self):
        metric_name = uuid.uuid4().hex
        val1 = random.uniform(1.0, 100.0)
        val2 = random.uniform(1.0, 100.0)

        data = [
            {"metric_name": metric_name, "value": val1},
            {"metric_name": metric_name, "value": val2}
        ]

        result = self.aggregator.aggregate_time_series(data)

        self.assertIn(metric_name, result)
        self.assertEqual(result[metric_name]["count"], 2)
        self.assertEqual(result[metric_name]["min"], min(val1, val2))
        self.assertEqual(result[metric_name]["max"], max(val1, val2))

    def test_aggregate_incidents_distribution(self):
        sev_levels = ["CRITICAL", "HIGH", "LOW"]
        incidents = [{"severity": random.choice(sev_levels)} for _ in range(10)]

        result = self.aggregator.aggregate_incidents(incidents)

        self.assertEqual(result["total_incidents"], 10)
        self.assertIsInstance(result["by_severity"], dict)

    def test_parse_html_health_report_extraction(self):
        rand_id = uuid.uuid4().hex
        rand_title = uuid.uuid4().hex
        html_content = f'<div class="incident-item" id="{rand_id}"><span class="title">{rand_title}</span></div>'

        stream = io.StringIO(html_content)
        result = self.aggregator.parse_html_health_report(stream)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], rand_id)
        self.assertEqual(result[0]["title"], rand_title)

    def test_fetch_external_health_data_success(self):
        url = f"https://{uuid.uuid4().hex}.com/api"
        mock_data = {"status": "ok", "val": random.randint(1, 100)}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response

            result = self.aggregator.fetch_external_health_data(url)
            self.assertEqual(result, mock_data)

    def test_export_prepared_dataset_io(self):
        file_path = f"{uuid.uuid4().hex}.json"
        data = {"test": random.random()}

        try:
            result = self.aggregator.export_prepared_dataset(data, file_path)
            self.assertTrue(result)
            with open(file_path, 'r') as f:
                loaded = json.load(f)
                self.assertEqual(loaded, data)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_aggregate_integration_flow(self):
        repo_id = uuid.uuid4().hex
        metric_id = uuid.uuid4().hex
        data_dir = uuid.uuid4().hex
        os.makedirs(data_dir, exist_ok=True)

        try:
            metric_file = os.path.join(data_dir, f"metrics_{uuid.uuid4().hex}.json")
            with open(metric_file, 'w') as f:
                json.dump({"metric_id": metric_id}, f)

            with patch('skills.repo_health_incident_tracker.RepoHealthIncidentTracker') as mock_tracker_cls:
                mock_tracker = mock_tracker_cls.return_value
                inc_id = uuid.uuid4().hex
                mock_tracker.get_incidents_by_repo.return_value = [{"incident_id": inc_id}]

                result = self.aggregator.aggregate(repo_id, data_dir)

                self.assertEqual(result["repo_id"], repo_id)
                self.assertEqual(result["metric_id"], metric_id)
                self.assertIn(inc_id, result["associated_incidents"])
        finally:
            for f in os.listdir(data_dir):
                os.remove(os.path.join(data_dir, f))
            os.rmdir(data_dir)

if __name__ == '__main__':
    unittest.main()