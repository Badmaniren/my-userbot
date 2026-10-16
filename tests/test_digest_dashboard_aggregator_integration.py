import unittest
import os
import uuid
import random
import tempfile

from skills.digest_dashboard_aggregator import DigestDashboardAggregator
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter


class TestDigestDashboardAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.random_id = str(uuid.uuid4())
        self.metric_value = random.randint(100, 9999)

        self.sample_digest = {
            "id": self.random_id,
            "metric": self.metric_value,
            "status": "unstable",
            "anomalies": [
                {"code": f"ERR-{random.randint(10, 99)}", "severity": "HIGH"}
            ]
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dashboard_aggregator_composition_real_run(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        exporter = DigestExporter(stability_digest=self.sample_digest, anomaly_visualizer=visualizer)

        aggregator = DigestDashboardAggregator(
            anomaly_visualizer=visualizer,
            digest_exporter=exporter
        )

        json_filename = f"report_{uuid.uuid4()}.json"
        json_path = os.path.join(self.test_dir.name, json_filename)

        html_filename = f"report_{uuid.uuid4()}.html"
        html_path = os.path.join(self.test_dir.name, html_filename)

        dashboard_data = aggregator.aggregate(
            json_output_path=json_path,
            html_output_path=html_path
        )

        self.assertIsInstance(dashboard_data, dict)
        self.assertIn("summary", dashboard_data)

        self.assertTrue(os.path.exists(json_path), "JSON report was not created by the integrated skills")
        self.assertTrue(os.path.exists(html_path), "HTML report was not created by the integrated skills")

        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content)
            self.assertIn(str(self.metric_value), content)


if __name__ == "__main__":
    unittest.main()