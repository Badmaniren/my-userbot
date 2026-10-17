import unittest
import os
import tempfile
import uuid
import random

from skills.digest_exporter import DigestExporter
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_dashboard_aggregator import DigestDashboardAggregator


class TestDigestDashboardAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

        self.random_id = str(uuid.uuid4())
        self.metric_value = random.randint(100, 999)
        
        self.digest_data = {
            "id": self.random_id,
            "metrics": {
                "stability_score": self.metric_value,
                "error_rate": random.random()
            },
            "anomalies": [
                {
                    "source": f"service_{random.randint(1, 10)}",
                    "severity": "HIGH",
                    "details": f"Test anomaly details {uuid.uuid4()}"
                }
            ]
        }

        self.visualizer = AnomalyVisualizer(self.digest_data)
        self.exporter = DigestExporter(stability_digest=self.digest_data, anomaly_visualizer=self.visualizer)

    def test_dashboard_aggregator_integration(self):
        aggregator = DigestDashboardAggregator(
            digest_exporter=self.exporter,
            anomaly_visualizer=self.visualizer
        )

        output_filename = f"dashboard_{uuid.uuid4()}.html"
        output_path = os.path.join(self.test_dir.name, output_filename)

        dashboard_result = aggregator.generate_operator_dashboard(output_path)

        self.assertTrue(os.path.exists(output_path), "Файл дашборда не был создан")
        
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content, "Случайный ID дайджеста не найден в сгенерированном дашборде")
            self.assertIn(str(self.metric_value), content, "Метрика стабильности не найдена в дашборде")

        self.assertIsInstance(dashboard_result, str, "Результат генерации дашборда должен быть строкой (путь или отчет)")


if __name__ == "__main__":
    unittest.main()