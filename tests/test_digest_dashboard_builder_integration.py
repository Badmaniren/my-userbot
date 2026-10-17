import unittest
import os
import tempfile
import uuid
import random

from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter
from skills.digest_dashboard_builder import DigestDashboardBuilder

class TestDigestDashboardBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)
        
        self.rand_str = str(uuid.uuid4())
        self.metric_value = random.randint(100, 999)
        
        self.sample_data = {
            "id": self.rand_str,
            "metric": self.metric_value,
            "status": "nominal" if random.random() > 0.5 else "degraded"
        }
        
        self.visualizer = AnomalyVisualizer(digest=self.sample_data)
        self.exporter = DigestExporter(stability_digest=self.sample_data, anomaly_visualizer=self.visualizer)
        
        self.dashboard_builder = DigestDashboardBuilder(
            anomaly_visualizer=self.visualizer,
            digest_exporter=self.exporter
        )

    def test_full_dashboard_builder_cycle(self):
        json_path = os.path.join(self.test_dir.name, f"dashboard_{self.rand_str}.json")
        html_path = os.path.join(self.test_dir.name, f"dashboard_{self.rand_str}.html")
        
        result = self.dashboard_builder.build_dashboard(json_output_path=json_path, html_output_path=html_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("reports", result)
        
        self.assertTrue(os.path.exists(json_path), "JSON дашборд не был создан в результате сборки")
        self.assertTrue(os.path.exists(html_path), "HTML дашборд не был создан в результате сборки")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.rand_str, content, "Случайный UUID дайджеста отсутствует в экспортированном JSON дашборде")
            self.assertIn(str(self.metric_value), content, "Случайное значение метрики отсутствует в экспортированном JSON дашборде")

if __name__ == '__main__':
    unittest.main()