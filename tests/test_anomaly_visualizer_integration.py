import unittest
import os
import uuid
import random
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyVisualizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_log_path = f"test_anomaly_log_{uuid.uuid4()}.json"
        self.test_export_path = f"test_report_{uuid.uuid4()}.txt"
        self.logger = AnomalyLogger(log_path=self.test_log_path)

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            try:
                os.remove(self.test_log_path)
            except OSError:
                pass
        if os.path.exists(self.test_export_path):
            try:
                os.remove(self.test_export_path)
            except OSError:
                pass

    def test_integration_visualizer_with_logger_and_correlator_flow(self):
        random_digest_id = str(uuid.uuid4())
        random_title = f"System Instability Test {uuid.uuid4().hex[:8]}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        source_name = f"service_{uuid.uuid4().hex[:4]}"
        target_name = f"service_{uuid.uuid4().hex[:4]}"
        coefficient = round(random.uniform(0.1, 0.99), 2)

        self.logger.log_anomaly(
            source=source_name,
            severity=random_severity,
            details="High latency detected during peak load.",
            telemetry_snapshot={"cpu": random.randint(70, 99)}
        )

        anomalies_list = self.logger.get_anomalies()
        
        visualizer = AnomalyVisualizer()
        logger_visualization_output = visualizer.visualize_digest(anomalies_list)

        self.assertIn("--- Anomaly Logger Digest ---", logger_visualization_output)
        self.assertIn(source_name, logger_visualization_output)
        self.assertIn(random_severity, logger_visualization_output)

        complex_digest = {
            "digest_id": random_digest_id,
            "title": random_title,
            "severity": random_severity,
            "metrics": {
                "error_rate": round(random.uniform(1.0, 15.0), 2),
                "active_connections": random.randint(100, 5000)
            },
            "correlations": [
                {
                    "source": source_name,
                    "target": target_name,
                    "coefficient": coefficient
                }
            ]
        }

        visualizer_digest_output = visualizer.visualize_digest(complex_digest)
        self.assertIn(random_digest_id, visualizer_digest_output)
        self.assertIn(random_title, visualizer_digest_output)

        ascii_graph = visualizer.render_ascii_correlation_graph()
        self.assertIn("--- ASCII Correlation Graph ---", ascii_graph)
        self.assertIn(source_name, ascii_graph)
        self.assertIn(target_name, ascii_graph)
        self.assertIn(str(coefficient), ascii_graph)

        exported_file = visualizer.export_report(self.test_export_path)
        self.assertEqual(exported_file, self.test_export_path)
        self.assertTrue(os.path.exists(self.test_export_path))

        with open(self.test_export_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(random_digest_id, file_content)
        self.assertIn(target_name, file_content)
        self.assertIn(str(coefficient), file_content)

if __name__ == "__main__":
    unittest.main()