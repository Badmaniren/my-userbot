import unittest
import os
import json
import uuid
import shutil
from skills.repo_health_predictor_pipeline import repo_health_predictor_pipeline

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "reports"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_pipeline_integration_flow(self):
        # Генерируем случайные данные для исключения хардкода
        repo_id = str(uuid.uuid4())
        raw_data = {
            "repository_id": repo_id,
            "metrics": {
                "commit_frequency": 0.8,
                "issue_resolution_time": 120
            }
        }

        # Вызов целевого модуля
        result = repo_health_predictor_pipeline(raw_data)

        # Проверка структуры ответа
        self.assertEqual(result["repository_id"], repo_id)
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["prediction_score"], float)
        self.assertTrue(0.0 <= result["prediction_score"] <= 1.0)

        # Проверка побочного эффекта (создание файла)
        expected_file_path = os.path.join(self.test_dir, f"health_prediction_{repo_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Файл отчета не был создан")

        # Проверка содержимого файла
        with open(expected_file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["repository_id"], repo_id)
            self.assertEqual(saved_data["prediction_score"], result["prediction_score"])

    def test_pipeline_invalid_input(self):
        # Проверка обработки пустого ввода
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

if __name__ == "__main__":
    unittest.main()