import unittest
import os
import json
import uuid
import random
import shutil
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.calculator = RepoHealthTrendCalculator()
        self.repo_id = str(uuid.uuid4())

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_lifecycle_integration(self):
        # 1. Подготовка случайных данных
        input_file = os.path.join(self.test_dir, f"input_{uuid.uuid4().hex}.json")
        output_file = os.path.join(self.test_dir, f"output_{uuid.uuid4().hex}.json")
        
        history = []
        for i in range(5):
            history.append({
                "snapshot_id": str(uuid.uuid4()),
                "metrics": {
                    "coverage": random.randint(50, 90),
                    "vulnerabilities": random.randint(0, 10)
                }
            })
        
        data = {"repo_id": self.repo_id, "history": history}
        
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # 2. Вызов функции интеграции
        result = calculate_health_trends(input_file, output_file)

        # 3. Проверка корректности возвращаемых данных
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertIn("trends", result)
        self.assertIn("summary", result)
        self.assertIn("coverage", result["trends"])
        self.assertIn("vulnerabilities", result["trends"])

        # 4. Проверка записи файла
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["repo_id"], self.repo_id)

    def test_anomaly_detection_integration(self):
        # Проверка работы методов класса с реальными данными
        history = [
            {"metrics": {"latency": 100}},
            {"metrics": {"latency": 105}},
            {"metrics": {"latency": 102}},
            {"metrics": {"latency": 500}}  # Аномалия
        ]
        
        anomalies = self.calculator.detect_metric_anomalies(history, "latency", z_threshold=1.0)
        
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metrics"]["latency"], 500)

    def test_export_summary_file_creation(self):
        # Проверка создания структуры папок и файла через метод класса
        output_path = os.path.join(self.test_dir, "subdir", f"{uuid.uuid4().hex}.json")
        history = [{"metrics": {"score": 10}}]
        
        success = self.calculator.export_trend_summary(history, output_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, "r", encoding="utf-8") as f:
            content = json.load(f)
            self.assertIn("overall_status", content)

if __name__ == "__main__":
    unittest.main()