import unittest
import os
import tempfile
import uuid
import random
from skills.digest_dashboard_generator import DigestDashboardGenerator, DigestDashboardGeneratorError

class TestDigestDashboardGeneratorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        
        self.random_stream_id = f"stream-{uuid.uuid4()}"
        self.random_metric_val = random.randint(100, 999)
        
        self.sample_digest = {
            "stream_id": self.random_stream_id,
            "metrics": {
                "stability_score": self.random_metric_val,
                "anomalies_count": random.randint(0, 5)
            },
            "anomalies": [
                {
                    "id": str(uuid.uuid4()),
                    "severity": "HIGH",
                    "description": "Integration test anomaly"
                }
            ],
            "streams": {
                self.random_stream_id: {
                    "status": "active",
                    "load": random.randint(10, 100)
                }
            }
        }
        
        self.generator = DigestDashboardGenerator(stability_digest=self.sample_digest)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_dashboard_generation_integration(self):
        json_filename = f"dashboard_{uuid.uuid4()}.json"
        html_filename = f"dashboard_{uuid.uuid4()}.html"
        
        json_path = os.path.join(self.test_dir.name, json_filename)
        html_path = os.path.join(self.test_dir.name, html_filename)
        
        self.assertFalse(os.path.exists(json_path))
        self.assertFalse(os.path.exists(html_path))
        
        result = self.generator.generate_dashboard(json_path, html_path)
        
        self.assertIn('json_report', result)
        self.assertIn('html_report', result)
        
        self.assertTrue(os.path.exists(json_path), "JSON файл отчета должен быть создан реально на диске")
        self.assertTrue(os.path.exists(html_path), "HTML файл отчета должен быть создан реально на диске")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = f.read()
            self.assertIn(str(self.random_metric_val), json_content)

    def test_metrics_summary_and_ascii_graph_integration(self):
        summary = self.generator.get_metrics_summary()
        self.assertIsInstance(summary, dict)
        
        ascii_graph = self.generator.render_ascii_graph()
        self.assertIsInstance(ascii_graph, str)

    def test_export_stream_integration(self):
        stream_filename = f"stream_{uuid.uuid4()}.json"
        stream_path = os.path.join(self.test_dir.name, stream_filename)
        
        self.assertFalse(os.path.exists(stream_path))
        
        res_path = self.generator.export_stream(self.random_stream_id, stream_path)
        
        self.assertTrue(os.path.exists(res_path))
        with open(res_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.random_stream_id, content)

    def test_individual_html_json_generators_integration(self):
        json_file = os.path.join(self.test_dir.name, f"sub_{uuid.uuid4()}.json")
        html_file = os.path.join(self.test_dir.name, f"sub_{uuid.uuid4()}.html")
        
        res_json = self.generator.generate_json_dashboard(json_file)
        res_html = self.generator.generate_html_dashboard(html_file)
        
        self.assertTrue(os.path.exists(res_json))
        self.assertTrue(os.path.exists(res_html))

    def test_generator_error_handling(self):
        with self.assertRaises(DigestDashboardGeneratorError):
            self.generator.generate_dashboard("", "")

if __name__ == '__main__':
    unittest.main()