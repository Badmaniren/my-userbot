import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.patch_evaluator import patch_evaluator
from skills.git_inspector import GitInspector
from skills.anomaly_logger import AnomalyLogger


class TestPatchEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем реальный репозиторий через GitInspector или базовые файлы
        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        
        self.target_file = os.path.join(self.repo_path, f"module_{uuid.uuid4().hex[:8]}.py")
        self.initial_content = f"# Initial content {uuid.uuid4()}\nx = {random.randint(1, 100)}\n"
        with open(self.target_file, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        self.log_path = os.path.join(self.test_dir, f"anomaly_log_{uuid.uuid4().hex}.json")
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.git_inspector = GitInspector(repo_path=self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_evaluator_real_integration(self):
        # Генерируем уникальные данные для патча
        random_id = uuid.uuid4().hex
        patch_content = f"# Patch update {random_id}\nx = {random.randint(101, 1000)}\n"
        
        # Записываем изменения в файл (симуляция применения патча)
        with open(self.target_file, "w", encoding="utf-8") as f:
            f.write(patch_content)

        # Проверяем работу git_inspector в связке с модулем
        history = self.git_inspector.get_history()
        self.assertIsNotNone(history)

        # Логируем телеметрию/аномалию для проверки взаимодействия с логгером
        severity_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)
        self.logger.log_anomaly(
            source="patch_evaluator_test",
            severity=chosen_severity,
            details=f"Evaluating patch {random_id}",
            telemetry_snapshot={"file": self.target_file, "random_val": random_id}
        )

        reports = self.logger.get_anomalies()
        self.assertTrue(any(random_id in str(rep) for rep in reports))

        # Вызываем тестируемый модуль patch_evaluator для оценки изменений
        # Передаем реальные пути и контекст без моков
        evaluation_result = patch_evaluator(
            repo_path=self.repo_path,
            patch_data=patch_content,
            target_file=self.target_file
        )

        self.assertIsNotNone(evaluation_result)
        
        # Проверяем структурированный отчет логгера
        structured_report = self.logger.get_structured_report()
        self.assertIsNotNone(structured_report)


if __name__ == "__main__":
    unittest.main()