import unittest
import os
import uuid
import random
import tempfile
from skills.digest_dashboard_generator import DigestDashboardGenerator
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter

class TestDigestDashboardGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)
        
        self.unique_id = str(uuid.uuid4())
        self.random_metric = random.randint(100, 999)
        
        self.sample_digest = {
            "id": self.unique_id,
            "metric_value": self.random_metric,
            "status": "active",
            "anomalies": [
                {
                    "source": "test_source",
                    "severity": "HIGH",
                    "details": f"Random error details {self.unique_id}",
                    "telemetry_snapshot": {"cpu": self.random_metric}
                }
            ]
        }
        
        self.visualizer = AnomalyVisualizer(digest=self.sample_digest)
        self.exporter = DigestExporter(stability_digest=self.sample_digest, anomaly_visualizer=self.visualizer)
        
        self.dashboard_generator = DigestDashboardGenerator(
            stability_digest=self.sample_digest,
            anomaly_visualizer=self.visualizer,
            digest_exporter=self.exporter
        )

    def test_dashboard_generation_integration(self):
        html_filename = f"dashboard_{self.unique_id}.html"
        json_filename = f"dashboard_{self.unique_id}.json"
        
        html_path = os.path.join(self.test_dir.name, html_filename)
        json_path = os.path.join(self.test_dir.name, json_filename)
        
        result_html = self.dashboard_generator.generate_html_dashboard(html_path)
        result_json = self.dashboard_generator.generate_json_dashboard(json_path)
        
        self.assertTrue(os.path.exists(html_path), "HTML dashboard file was not created on disk.")
        self.assertTrue(os.path.exists(json_path), "JSON dashboard file was not created on disk.")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            self.assertIn(self.unique_id, html_content, "Generated HTML does not contain the unique test ID.")
            self.assertIn(str(self.random_metric), html_content, "Generated HTML does not contain the random metric.")
            
        with open(json_path, "r", encoding="utf-8") as f:
            json_content = f.read()
            self.assertIn(self.unique_id, json_content, "Generated JSON does not contain the unique test ID.")
            
        self.assertIn(html_filename, result_html)
        self.assertIn(json_filename, result_json)

if __name__ == "__main__":
    unittest.main()