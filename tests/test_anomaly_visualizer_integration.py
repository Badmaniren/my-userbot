import unittest
import os
import uuid
import random
from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyVisualizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_logs_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.log_path = os.path.join(self.test_dir, f"anomalies_{uuid.uuid4().hex}.json")
        self.logger = AnomalyLogger(self.log_path)
        self.visualizer = AnomalyVisualizer()

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_integration_logger_to_visualizer_pipeline(self):
        random_source = f"service_{uuid.uuid4().hex[:6]}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = f"Anomaly detected with metric value {random.randint(100, 9999)}"
        
        self.logger.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot={"cpu_load": random.random()}
        )
        
        anomalies_list = self.logger.get_anomalies()
        
        visual_output = self.visualizer.visualize_digest(anomalies_list)
        
        self.assertIn("--- Anomaly Logger Digest ---", visual_output)
        self.assertIn(random_source, visual_output)
        self.assertIn(random_severity, visual_output)
        self.assertIn(random_details, visual_output)

    def test_integration_digest_rendering_and_export(self):
        digest_id = str(uuid.uuid4())
        title = f"Report Title {uuid.uuid4().hex[:4]}"
        severity = random.choice(["INFO", "WARNING", "FATAL"])
        metric_key = f"metric_{uuid.uuid4().hex[:4]}"
        metric_val = random.randint(1, 1000)
        
        source_node = f"node_{uuid.uuid4().hex[:4]}"
        target_node = f"node_{uuid.uuid4().hex[:4]}"
        coef = round(random.uniform(0.1, 0.99), 2)

        digest_data = {
            "digest_id": digest_id,
            "title": title,
            "severity": severity,
            "metrics": {
                metric_key: metric_val
            },
            "correlations": [
                {
                    "source": source_node,
                    "target": target_node,
                    "coefficient": coef
                }
            ]
        }

        self.visualizer.visualize_digest(digest_data)
        
        rendered_text = self.visualizer.render_text()
        self.assertIn(digest_id, rendered_text)
        self.assertIn(title, rendered_text)
        self.assertIn(severity, rendered_text)
        self.assertIn(f"{metric_key}: {metric_val}", rendered_text)

        graph_text = self.visualizer.render_ascii_correlation_graph()
        self.assertIn("--- ASCII Correlation Graph ---", graph_text)
        self.assertIn(source_node, graph_text)
        self.assertIn(target_node, graph_text)
        self.assertIn(str(coef), graph_text)

        export_file_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.txt")
        try:
            returned_path = self.visualizer.export_report(export_file_path)
            self.assertEqual(returned_path, export_file_path)
            self.assertTrue(os.path.exists(export_file_path))
            
            with open(export_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(digest_id, content)
                self.assertIn(source_node, content)
        finally:
            if os.path.exists(export_file_path):
                os.remove(export_file_path)

if __name__ == "__main__":
    unittest.main()