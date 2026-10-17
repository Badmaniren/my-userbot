import os
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

from skills.anomaly_logger import AnomalyLogger
from skills.patch_checker import PatchChecker
from skills.patch_quality_aggregator import PatchQualityAggregator


class TestPatchQualityAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_file = os.path.join(self.repo_path, f"anomalies_{uuid.uuid4().hex}.json")

        # Инициализация реального git-репозитория для PatchChecker
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "IntegrationTester"], cwd=self.repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=self.repo_path, check=True)

        # Создание базового файла в репозитории
        self.target_file = f"sample_{uuid.uuid4().hex[:8]}.py"
        self.initial_token = f"init_{uuid.uuid4().hex}"
        target_path = Path(self.repo_path) / self.target_file
        target_path.write_text(f"# Initial code: {self.initial_token}\n", encoding="utf-8")

        subprocess.run(["git", "add", self.target_file], cwd=self.repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, check=True)

        # Реальные экземпляры зависимостей
        self.checker = PatchChecker(repo_path=self.repo_path, policy={})
        self.logger = AnomalyLogger(log_path=self.log_file)

        # Агрегатор объединяет оба компонента
        self.aggregator = PatchQualityAggregator(checker=self.checker, logger=self.logger)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_aggregate_valid_patch_workflow(self):
        unique_patch_id = f"valid_{uuid.uuid4().hex}"
        patch_content = (
            f"--- a/{self.target_file}\n"
            f"+++ b/{self.target_file}\n"
            f"@@ -1,1 +1,2 @@\n"
            f" # Initial code: {self.initial_token}\n"
            f"+# Feature add: {unique_patch_id}\n"
        )

        result = self.aggregator.aggregate(patch_content=patch_content, target_file=self.target_file)

        self.assertIsInstance(result, dict)
        self.assertIn("quality_score", result)
        self.assertIn("checker_result", result)
        self.assertIn("anomalies_count", result)
        self.assertEqual(result["anomalies_count"], 0)

        # Проверка, что логгер остался чистым при успешном патче
        anomalies = self.logger.get_anomalies()
        self.assertEqual(len(anomalies), 0)

    def test_aggregate_malformed_patch_logs_anomaly_and_updates_storage(self):
        corrupt_marker = f"corrupt_{uuid.uuid4().hex}"
        malformed_patch = f"INVALID_DIFF_HEADER_{corrupt_marker}\n@@ non-existent @@\n"

        result = self.aggregator.aggregate(patch_content=malformed_patch, target_file=self.target_file)

        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)
        self.assertFalse(result["is_safe"])
        self.assertGreaterEqual(result["anomalies_count"], 1)

        # Проверка фиксации аномалии в AnomalyLogger без моков
        anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1)

        # Проверяем, что файл журнала был физически создан на диске
        self.assertTrue(os.path.exists(self.log_file))
        file_content = Path(self.log_file).read_text(encoding="utf-8")
        self.assertIn("patch_checker", file_content)

        # Проверка структурированного отчета логгера через агрегатор
        report = self.logger.get_structured_report()
        self.assertIsInstance(report, dict)
        self.assertIn("total_anomalies", report)
        self.assertGreaterEqual(report["total_anomalies"], 1)


if __name__ == "__main__":
    unittest.main()