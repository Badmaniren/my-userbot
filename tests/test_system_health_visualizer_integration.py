import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_visualizer import system_health_visualizer
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.system_health_aggregator import system_health_aggregator

class TestSystemHealthVisualizerIntegration(unittest.TestCase):
    def test_health_visualization_pipeline(self):
        random_node_id = f"node-{uuid.uuid4()}"
        random_cpu_load = round(random.uniform(10.0, 99.9), 2)
        random_memory_usage = round(random.uniform(20.0, 95.5), 2)
        
        telemetry_data = {
            "node_id": random_node_id,
            "metrics": {
                "cpu_load": random_cpu_load,
                "memory_usage": random_memory_usage
            }
        }
        
        collected_telemetry = system_health_telemetry_collector(telemetry_data)
        self.assertIsNotNone(collected_telemetry)
        
        aggregated_health = system_health_aggregator(collected_telemetry)
        self.assertIn("status", aggregated_health)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            random_chart_name = f"health_chart_{uuid.uuid4()}.png"
            output_path = os.path.join(temp_dir, random_chart_name)
            
            visualization_result = system_health_visualizer(aggregated_health, output_path=output_path)
            
            self.assertTrue(os.path.exists(output_path), "График состояния системы не был создан на диске.")
            self.assertEqual(visualization_result.get("target_node"), random_node_id)
            self.assertIn(str(random_cpu_load), str(visualization_result.get("rendered_metrics", "")))

if __name__ == "__main__":
    unittest.main()