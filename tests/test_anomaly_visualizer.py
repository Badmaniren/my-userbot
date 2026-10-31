import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import string
import os

from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError


class TestAnomalyVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_digest_id = uuid.uuid4().hex
        self.random_title = f"Title_{uuid.uuid4().hex[:8]}"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        self.metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(1.0, 100.0), 2)
        
        self.source_node = f"node_{uuid.uuid4().hex[:6]}"
        self.target_node = f"node_{uuid.uuid4().hex[:6]}"
        self.coef = round(random.uniform(0.1, 0.99), 2)

        self.sample_digest = {
            "digest_id": self.random_digest_id,
            "title": self.random_title,
            "severity": self.random_severity,
            "metrics": {
                self.metric_key: self.metric_value
            },
            "correlations": [
                {
                    "source": self.source_node,
                    "target": self.target_node,
                    "coefficient": self.coef
                }
            ]
        }

    def test_init_valid_digest(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        self.assertEqual(visualizer.digest, self.sample_digest)

    def test_init_invalid_digest_raises_error(self):
        invalid_digest = random.choice([
            uuid.uuid4().hex,
            random.randint(1000, 9999),
            [random.randint(1, 10)]
        ])
        with self.assertRaises(AnomalyVisualizerError):
            AnomalyVisualizer(digest=invalid_digest)

    def test_init_empty_digest(self):
        visualizer = AnomalyVisualizer()
        self.assertEqual(visualizer.digest, {})

    def test_render_text_contains_digest_data(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        rendered = visualizer.render_text()

        self.assertIn(self.random_digest_id, rendered)
        self.assertIn(self.random_title, rendered)
        self.assertIn(self.random_severity, rendered)
        self.assertIn(self.metric_key, rendered)
        self.assertIn(str(self.metric_value), rendered)
        self.assertIn(self.source_node, rendered)
        self.assertIn(self.target_node, rendered)
        self.assertIn(str(self.coef), rendered)

    def test_render_ascii_correlation_graph_success(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        graph = visualizer.render_ascii_correlation_graph()

        self.assertIn("--- ASCII Correlation Graph ---", graph)
        self.assertIn(self.source_node, graph)
        self.assertIn(self.target_node, graph)
        self.assertIn(f"{self.coef:.2f}", graph)

    def test_render_ascii_correlation_graph_empty(self):
        empty_digest = {"correlations": []}
        visualizer = AnomalyVisualizer(digest=empty_digest)
        graph = visualizer.render_ascii_correlation_graph()
        self.assertEqual(graph, "No correlations available.")

    def test_get_summary_metrics(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        metrics = visualizer.get_summary_metrics()
        self.assertEqual(metrics, {self.metric_key: self.metric_value})

    def test_visualize_digest_with_dict(self):
        visualizer = AnomalyVisualizer()
        result = visualizer.visualize_digest(self.sample_digest)
        self.assertEqual(visualizer.digest, self.sample_digest)
        self.assertIn(self.random_digest_id, result)

    def test_visualize_digest_with_list(self):
        visualizer = AnomalyVisualizer()
        anomaly_list = [
            {
                "source": f"src_{uuid.uuid4().hex[:5]}",
                "severity": random.choice(["INFO", "WARN"]),
                "details": f"detail_{uuid.uuid4().hex[:8]}"
            }
        ]
        result = visualizer.visualize_digest(anomaly_list)
        self.assertIn("--- Anomaly Logger Digest ---", result)
        self.assertIn(anomaly_list[0]["source"], result)
        self.assertIn(anomaly_list[0]["severity"], result)
        self.assertIn(anomaly_list[0]["details"], result)

    def test_visualize_digest_with_other_type(self):
        visualizer = AnomalyVisualizer()
        random_string = "".join(random.choices(string.ascii_letters, k=12))
        result = visualizer.visualize_digest(random_string)
        self.assertEqual(result, random_string)

    def test_export_report_success(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        target_path = f"/tmp/{uuid.uuid4().hex}.txt"

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            path_result = visualizer.export_report(target_path)

        self.assertEqual(path_result, target_path)
        mock_file.assert_called_once_with(target_path, "w", encoding="utf-8")
        
        handle = mock_file()
        handle.write.assert_called()

    def test_export_report_io_error_raises_exception(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        target_path = f"/tmp/{uuid.uuid4().hex}.txt"

        with patch("builtins.open", side_effect=IOError("Disk full")):
            with self.assertRaises(AnomalyVisualizerError) as ctx:
                visualizer.export_report(target_path)
            self.assertIn("Failed to export report", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()