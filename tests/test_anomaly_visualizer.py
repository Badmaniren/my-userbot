import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import os
from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError

class TestAnomalyVisualizerInquisition(unittest.TestCase):

    def setUp(self):
        self.random_digest_id = uuid.uuid4().hex
        self.random_title = f"Title_{uuid.uuid4().hex[:6]}"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        self.metric_key = f"metric_{uuid.uuid4().hex[:4]}"
        self.metric_val = random.randint(10, 1000)
        
        self.source_node = f"src_{uuid.uuid4().hex[:4]}"
        self.target_node = f"tgt_{uuid.uuid4().hex[:4]}"
        self.coef = round(random.uniform(0.1, 1.0), 2)
        
        self.sample_digest = {
            "digest_id": self.random_digest_id,
            "title": self.random_title,
            "severity": self.random_severity,
            "metrics": {
                self.metric_key: self.metric_val
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

    def test_init_none_digest(self):
        visualizer = AnomalyVisualizer(digest=None)
        self.assertEqual(visualizer.digest, {})

    def test_init_invalid_digest_type(self):
        invalid_digest = uuid.uuid4().hex
        with self.assertRaises(AnomalyVisualizerError):
            AnomalyVisualizer(digest=invalid_digest)

    def test_render_text(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        rendered = visualizer.render_text()
        
        self.assertIn(self.random_digest_id, rendered)
        self.assertIn(self.random_title, rendered)
        self.assertIn(self.random_severity, rendered)
        self.assertIn(self.metric_key, rendered)
        self.assertIn(str(self.metric_val), rendered)
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

    def test_export_report(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        target_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            res_path = visualizer.export_report(target_path)
            
        self.assertEqual(res_path, target_path)
        mock_file.assert_called_once_with(target_path, "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_called()

    def test_export_report_io_error(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        target_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        with patch("builtins.open", side_effect=IOError("Disk full")):
            with self.assertRaises(AnomalyVisualizerError):
                visualizer.export_report(target_path)

    def test_get_summary_metrics(self):
        visualizer = AnomalyVisualizer(digest=self.sample_digest)
        metrics = visualizer.get_summary_metrics()
        self.assertEqual(metrics, {self.metric_key: self.metric_val})

    def test_visualize_digest_list(self):
        visualizer = AnomalyVisualizer()
        anomaly_list = [
            {
                "source": f"src_{uuid.uuid4().hex[:4]}",
                "severity": random.choice(["LOW", "HIGH"]),
                "details": f"det_{uuid.uuid4().hex[:6]}"
            }
        ]
        res = visualizer.visualize_digest(anomaly_list)
        self.assertIn("--- Anomaly Logger Digest ---", res)
        self.assertIn(anomaly_list[0]["source"], res)
        self.assertIn(anomaly_list[0]["severity"], res)
        self.assertIn(anomaly_list[0]["details"], res)

    def test_visualize_digest_dict(self):
        visualizer = AnomalyVisualizer()
        res = visualizer.visualize_digest(self.sample_digest)
        self.assertEqual(visualizer.digest, self.sample_digest)
        self.assertIn(self.random_digest_id, res)

    def test_visualize_digest_other_type(self):
        visualizer = AnomalyVisualizer()
        random_string = uuid.uuid4().hex
        res = visualizer.visualize_digest(random_string)
        self.assertEqual(res, random_string)