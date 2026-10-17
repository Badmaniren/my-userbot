import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import os
from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError

class TestAnomalyVisualizer(unittest.TestCase):
    def setUp(self):
        self.digest_id = uuid.uuid4().hex
        self.title = f"Title-{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.metric_key = uuid.uuid4().hex[:8]
        self.metric_val = random.randint(1, 1000)
        self.source = uuid.uuid4().hex[:6]
        self.target = uuid.uuid4().hex[:6]
        self.coef = round(random.random(), 2)

        self.sample_digest = {
            "digest_id": self.digest_id,
            "title": self.title,
            "severity": self.severity,
            "metrics": {
                self.metric_key: self.metric_val
            },
            "correlations": [
                {
                    "source": self.source,
                    "target": self.target,
                    "coefficient": self.coef
                }
            ]
        }

    def test_init_valid_digest(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        self.assertEqual(visualizer.digest, self.sample_digest)

    def test_init_none_digest(self):
        visualizer = AnomalyVisualizer(None)
        self.assertEqual(visualizer.digest, {})

    def test_init_invalid_digest_raises_error(self):
        invalid_digest = uuid.uuid4().hex
        with self.assertRaises(AnomalyVisualizerError):
            AnomalyVisualizer(invalid_digest)

    def test_render_text(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        text_output = visualizer.render_text()
        
        self.assertIn(self.digest_id, text_output)
        self.assertIn(self.title, text_output)
        self.assertIn(self.severity, text_output)
        self.assertIn(self.metric_key, text_output)
        self.assertIn(str(self.metric_val), text_output)
        self.assertIn(self.source, text_output)
        self.assertIn(self.target, text_output)

    def test_render_ascii_correlation_graph_with_data(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        graph_output = visualizer.render_ascii_correlation_graph()
        
        self.assertIn("--- ASCII Correlation Graph ---", graph_output)
        self.assertIn(self.source, graph_output)
        self.assertIn(self.target, graph_output)
        self.assertIn(f"{self.coef:.2f}", graph_output)

    def test_render_ascii_correlation_graph_empty(self):
        empty_digest = {"correlations": []}
        visualizer = AnomalyVisualizer(empty_digest)
        graph_output = visualizer.render_ascii_correlation_graph()
        
        self.assertEqual(graph_output, "No correlations available.")

    def test_get_summary_metrics(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        metrics = visualizer.get_summary_metrics()
        
        self.assertEqual(metrics, {self.metric_key: self.metric_val})

    def test_visualize_digest_with_dict(self):
        visualizer = AnomalyVisualizer()
        result = visualizer.visualize_digest(self.sample_digest)
        
        self.assertEqual(visualizer.digest, self.sample_digest)
        self.assertIn(self.digest_id, result)

    def test_visualize_digest_with_list(self):
        visualizer = AnomalyVisualizer()
        details_str = uuid.uuid4().hex
        anomaly_list = [
            {
                "source": self.source,
                "severity": self.severity,
                "details": details_str
            }
        ]
        result = visualizer.visualize_digest(anomaly_list)
        
        self.assertIn("--- Anomaly Logger Digest ---", result)
        self.assertIn(self.source, result)
        self.assertIn(self.severity, result)
        self.assertIn(details_str, result)

    def test_visualize_digest_with_other_type(self):
        visualizer = AnomalyVisualizer()
        random_number = random.randint(100, 999)
        result = visualizer.visualize_digest(random_number)
        
        self.assertEqual(result, str(random_number))

    def test_export_report_success(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        target_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            path = visualizer.export_report(target_path)
            
        mock_file.assert_called_once_with(target_path, "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_called()
        self.assertEqual(path, target_path)

    def test_export_report_io_error(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        target_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(AnomalyVisualizerError):
                visualizer.export_report(target_path)

if __name__ == "__main__":
    unittest.main()