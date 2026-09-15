import unittest
import os
import uuid
import tempfile
from skills.system_health_visualizer import SystemHealthVisualizer, system_health_visualizer

class TestSystemHealthVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.visualizer = SystemHealthVisualizer()
        self.system_id = f"sys_{uuid.uuid4().hex[:8]}"
        self.node_id = f"node_{uuid.uuid4().hex[:8]}"
        self.metric_value = uuid.uuid4().hex[:6]

    def test_visualize_critical_metrics_integration(self):
        result = self.visualizer.visualize_critical_metrics(self.system_id)
        self.assertIsInstance(result, dict)
        self.assertIn("chart_rendering", result)
        self.assertEqual(result["chart_rendering"], "success")

    def test_build_realtime_status_graph_integration(self):
        result = self.visualizer.build_realtime_status_graph(self.system_id)
        self.assertIsInstance(result, dict)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)

    def test_system_health_visualizer_functional_with_file_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "subdir", f"chart_{uuid.uuid4().hex[:6]}.txt")
            
            payload = {
                "node_id": self.node_id,
                "metrics": {"cpu_load": self.metric_value}
            }
            
            result = system_health_visualizer(payload, output_path=output_file)
            
            self.assertEqual(result["target_node"], self.node_id)
            self.assertIn(self.metric_value, result["rendered_metrics"])
            self.assertTrue(os.path.exists(output_file))
            
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertEqual(content, "CHART_DATA")

if __name__ == "__main__":
    unittest.main()