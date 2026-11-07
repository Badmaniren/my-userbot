import unittest
import uuid
import random
import os
from skills.repo_health_predictor_pipeline import repo_health_predictor_pipeline

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    def test_pipeline_execution(self):
        unique_repo_id = f"repo_{uuid.uuid4().hex[:8]}"
        metric_threshold = round(random.uniform(0.5, 0.95), 2)
        
        input_payload = {
            "repository_id": unique_repo_id,
            "historical_window_days": random.randint(30, 365),
            "confidence_threshold": metric_threshold,
            "target_environment": "integration_test"
        }

        result = repo_health_predictor_pipeline(input_payload)

        self.assertIsInstance(result, dict, "Конвейер должен возвращать словарь с результатами")
        self.assertIn("status", result, "Результат должен содержать статус выполнения")
        self.assertEqual(result.get("repository_id"), unique_repo_id, "Идентификатор репозитория должен совпадать с переданным")
        self.assertIn("prediction_score", result, "В результате должен присутствовать прогнозируемый показатель здоровья")
        self.assertIsInstance(result["prediction_score"], float, "Показатель прогноза должен быть числом с плавающей точкой")
        
        report_path = f"reports/health_prediction_{unique_repo_id}.json"
        if os.path.exists(report_path):
            self.assertTrue(os.path.isfile(report_path), "Артефакт отчета должен быть файлом")
            os.remove(report_path)

if __name__ == "__main__":
    unittest.main()