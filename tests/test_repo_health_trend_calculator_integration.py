import unittest
import json
import os
import uuid
import random
import shutil
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.calculator = RepoHealthTrendCalculator()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_pipeline_integration(self):
        repo_id = str(uuid.uuid4())
        input_file = os.path.join(self.test_dir, "input.json")
        output_file = os.path.join(self.test_dir, "output.json")

        # Генерация случайных данных истории
        history = []
        for i in range(5):
            history.append({
                "snapshot_id": str(uuid.uuid4()),
                "metrics": {
                    "coverage": random.uniform(50.0, 90.0),
                    "vulnerabilities": random.randint(0, 10)
                }
            })

        input_data = {"repo_id": repo_id, "history": history}
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(input_data, f)

        # Вызов функции интеграции
        result = calculate_health_trends(input_file, output_file)

        # Проверка корректности возвращаемых данных
        self.assertEqual(result["repo_id"], repo_id)
        self.assertIn("coverage", result["trends"])
        self.assertIn("vulnerabilities", result["trends"])
        self.assertIn("summary", result)

        # Проверка создания файла
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r", encoding="utf-8") as f:
            exported_data = json.load(f)
            self.assertEqual(exported_data["repo_id"], repo_id)

    def test_anomaly_detection_logic(self):
        # Генерация данных с явной аномалией
        history = [
            {"metrics": {"latency": 10}},
            {"metrics": {"latency": 12}},
            {"metrics": {"latency": 11}},
            {"metrics": {"latency": 100}}  # Аномалия
        ]
        
        anomalies = self.calculator.detect_metric_anomalies(history, "latency", z_threshold=1.0)
        
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metrics"]["latency"], 100)

    def test_smoothing_calculation(self):
        history = [
            {"metrics": {"score": 10.0}},
            {"metrics": {"score": 20.0}}
        ]
        # smoothing_factor = 0.5
        # val1 = 10.0
        # val2 = 0.5 * 20.0 + (1 - 0.5) * 10.0 = 15.0
        smoothed = self.calculator.get_smoothed_series(history, "score")
        
        self.assertEqual(len(smoothed), 2)
        self.assertEqual(smoothed[0], 10.0)
        self.assertEqual(smoothed[1], 15.0)

if __name__ == "__main__":
    unittest.main()