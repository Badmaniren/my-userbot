import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError


class TestAnomalyVisualizer(unittest.TestCase):

    def setUp(self):
        self.rand_digest_id = uuid.uuid4().hex
        self.rand_title = "".join(random.choices(string.ascii_letters, k=10))
        self.rand_metric_name = "".join(random.choices(string.ascii_lowercase, k=8))
        self.rand_metric_value = random.uniform(0.0, 100.0)
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        self.sample_digest = {
            "digest_id": self.rand_digest_id,
            "title": self.rand_title,
            "metrics": {
                self.rand_metric_name: self.rand_metric_value
            },
            "correlations": [
                {
                    "source": "".join(random.choices(string.ascii_letters, k=5)),
                    "target": "".join(random.choices(string.ascii_letters, k=5)),
                    "coefficient": random.uniform(-1.0, 1.0)
                }
            ],
            "severity": self.rand_severity
        }

    def test_visualizer_initialization_success(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        self.assertEqual(visualizer.digest["digest_id"], self.rand_digest_id)
        self.assertEqual(visualizer.digest["title"], self.rand_title)

    def test_visualizer_initialization_invalid_type_raises_error(self):
        bad_digest = "".join(random.choices(string.ascii_letters, k=12))
        with self.assertRaises(AnomalyVisualizerError):
            AnomalyVisualizer(bad_digest)

    def test_render_text_digest_contains_injected_data(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        output = visualizer.render_text()
        
        self.assertIn(self.rand_digest_id, output)
        self.assertIn(self.rand_title, output)
        self.assertIn(self.rand_metric_name, output)
        self.assertIn(str(self.rand_metric_value), output)
        self.assertIn(self.rand_severity, output)

    def test_render_ascii_correlation_graph_contains_elements(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        graph = visualizer.render_ascii_correlation_graph()
        
        correlation_item = self.sample_digest["correlations"][0]
        self.assertIn(correlation_item["source"], graph)
        self.assertIn(correlation_item["target"], graph)

    def test_export_to_file_writes_random_content(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        mock_file_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        mock_open_name = "builtins.open" if sys.version_info[0] >= 3 else "__builtin__.open"
        
        mock_file = MagicMock()
        with patch(mock_open_name, create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = mock_file
            
            result_path = visualizer.export_report(mock_file_path)
            
            mock_open.assert_called_once_with(mock_file_path, "w", encoding="utf-8")
            mock_file.write.assert_called()
            self.assertEqual(result_path, mock_file_path)

    def test_export_to_file_handles_io_error(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        mock_file_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        mock_open_name = "builtins.open" if sys.version_info[0] >= 3 else "__builtin__.open"
        
        with patch(mock_open_name, side_effect=IOError("Disk full")):
            with self.assertRaises(AnomalyVisualizerError):
                visualizer.export_report(mock_file_path)

    def test_summary_metrics_extraction(self):
        visualizer = AnomalyVisualizer(self.sample_digest)
        metrics = visualizer.get_summary_metrics()
        
        self.assertIn(self.rand_metric_name, metrics)
        self.assertEqual(metrics[self.rand_metric_name], self.rand_metric_value)

    def test_empty_digest_handling(self):
        empty_digest = {
            "digest_id": uuid.uuid4().hex,
            "title": "",
            "metrics": {},
            "correlations": [],
            "severity": "LOW"
        }
        visualizer = AnomalyVisualizer(empty_digest)
        text_out = visualizer.render_text()
        self.assertIn(empty_digest["digest_id"], text_out)
        
        graph_out = visualizer.render_ascii_correlation_graph()
        self.assertIsInstance(graph_out, str)


if __name__ == "__main__":
    unittest.main()