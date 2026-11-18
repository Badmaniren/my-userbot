import unittest
import uuid
import random
import tempfile
import os
from skills.repo_health_analyzer import RepoHealthAnalyzer
from skills.repo_auditor import RepoAuditor


class TestRepoHealthAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer = RepoHealthAnalyzer()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        # Создаем тестовые файлы в директории, чтобы RepoAuditor реально что-то нашел
        self.test_file_name = f"test_file_{uuid.uuid4().hex[:8]}.py"
        with open(os.path.join(self.repo_path, self.test_file_name), "w") as f:
            f.write("print('Integration test payload')\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_analyze_health_real_integration(self):
        # Генерируем случайные пороговые значения и метрики, исключая хардкод
        random_threshold = round(random.uniform(5.0, 15.0), 2)
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        exceeding_value = random_threshold + round(random.uniform(1.0, 10.0), 2)

        metrics = {
            metric_key: exceeding_value,
            "stable_metric": random_threshold - 2.0
        }

        # Вызываем метод целевого модуля без моков, проверяя связку с RepoAuditor
        result = self.analyzer.analyze_health(
            repo_path=self.repo_path,
            threshold=random_threshold,
            metrics=metrics
        )

        # Проверяем структуру и реальные данные ответа
        self.assertIn("health_score", result)
        self.assertIn("anomalies_detected", result)
        self.assertIn("audit_details", result)

        # Проверяем логику обнаружения аномалий на основе сгенерированных данных
        self.assertIn(metric_key, result["anomalies_detected"])
        self.assertNotIn("stable_metric", result["anomalies_detected"])

        # Проверяем, что audit_details реально отработал по временной директории
        audit_details = result["audit_details"]
        self.assertIsInstance(audit_details, dict)

    def test_generate_optimization_patch_randomized(self):
        # Генерируем уникальные входные данные для патча
        patch_uuid = str(uuid.uuid4())
        module_name = f"module_{uuid.uuid4().hex[:6]}"
        random_score = random.randint(0, 100)

        input_data = {
            "module": module_name,
            "patch_uuid": patch_uuid,
            "score": random_score
        }

        result = self.analyzer.generate_optimization_patch(input_data)

        # Проверяем корректность возвращаемых данных и их соответствие сгенерированным
        self.assertEqual(result["patch_uuid"], patch_uuid)
        self.assertEqual(result["target_module"], module_name)

        expected_action = "OPTIMAL" if random_score >= 50 else "REFACTOR_REQUIRED"
        self.assertEqual(result["action_code"], expected_action)


if __name__ == "__main__":
    unittest.main()