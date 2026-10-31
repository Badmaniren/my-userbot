import unittest
import os
import uuid
import random
import json
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_log_path = f"test_log_{uuid.uuid4().hex}.json"
        self.export_path = f"report_{uuid.uuid4().hex}.txt"
        self.logger = AnomalyLogger(log_path=self.test_log_path)
        self.visualizer = AnomalyVisualizer()

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)
        if os.path.exists(self.export_path):
            os.remove(self.export_path)

    def test_logger_to_visualizer_integration(self):
        # Генерируем случайные данные для аномалии
        source = f"service_{random.randint(100, 999)}"
        severity = random.choice(["CRITICAL", "WARNING", "INFO"])
        details = f"Random anomaly detected: {uuid.uuid4()}"
        
        # Логируем через AnomalyLogger
        self.logger.log_anomaly(source, severity, details, {"cpu": random.random()})
        anomalies = self.logger.get_anomalies()
        
        # Передаем данные в визуализатор
        report = self.visualizer.visualize_digest(anomalies)
        
        # Проверяем, что визуализатор корректно обработал данные из логгера
        self.assertIn(source, report)
        self.assertIn(severity, report)
        self.assertIn(details, report)

    def test_full_export_cycle(self):
        # Создаем сложный дайджест с корреляциями
        digest_id = str(uuid.uuid4())
        digest = {
            "digest_id": digest_id,
            "title": "System Stability Report",
            "severity": "HIGH",
            "metrics": {"latency": random.uniform(10, 100)},
            "correlations": [
                {"source": "node_a", "target": "node_b", "coefficient": random.random()}
            ]
        }
        
        visualizer = AnomalyVisualizer(digest=digest)
        
        # Экспортируем отчет в файл
        exported_file = visualizer.export_report(self.export_path)
        
        # Проверяем создание файла
        self.assertTrue(os.path.exists(exported_file))
        
        # Читаем файл и проверяем наличие данных
        with open(exported_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(digest_id, content)
            self.assertIn("ASCII Correlation Graph", content)

if __name__ == "__main__":
    unittest.main()