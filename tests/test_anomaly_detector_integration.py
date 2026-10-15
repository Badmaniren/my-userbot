import unittest
import uuid
import random
import tempfile
import shutil
import os
from pathlib import Path

from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.patch_executor import PatchExecutor
from skills.patch_verifier import PatchVerifier
from skills.anomaly_detector import AnomalyDetector


class TestAnomalyDetectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация реального репозитория (без моков)
        os.system(f"git init -b main {self.repo_path}")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

        # Генерация уникальных данных для теста
        self.unique_id = str(uuid.uuid4())
        self.metric_value = random.randint(100, 1000)
        
        # Создаем файл с историей для анализа GitInspector и LessonParser
        self.target_file = Path(self.repo_path) / "system_metric.py"
        self.target_file.write_text(f"# Lesson: optimization_{self.unique_id}\n# Metric: {self.metric_value}\n")
        
        os.system(f"git -C {self.repo_path} add system_metric.py")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit {self.unique_id}'")

        # Инициализация реальных связанных навыков
        self.git_inspector = GitInspector(self.repo_path)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.patch_executor = PatchExecutor(self.repo_path, self.git_inspector, self.lesson_parser)
        self.patch_verifier = PatchVerifier(self.repo_path, self.git_inspector, self.patch_executor)
        
        # Целевой модуль для тестирования
        self.anomaly_detector = AnomalyDetector(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_detect_anomalies_integration(self):
        # Создаем аномальный патч с рандомными данными
        patch_content = f"""
# Anomaly patch {self.unique_id}
def anomalous_function_{self.unique_id.replace('-', '_')}():
    return {self.metric_value * 10}
"""
        patch_data = {
            "file_path": "system_metric.py",
            "content": patch_content,
            "commit_message": f"Apply anomaly patch {self.unique_id}"
        }

        # Выполняем верификацию и применение через связанный стек навыков
        verification_result = self.patch_verifier.verify_and_apply(patch_data)
        self.assertTrue(verification_result, "Патч должен успешно пройти верификацию и примениться.")

        # Запускаем анализ аномалий на основе реальных метрик и истории
        anomalies = self.anomaly_detector.detect_anomalies()

        # Проверяем, что детектор вернул структурированный результат и зафиксировал изменения
        self.assertIsInstance(anomalies, dict, "Результат должен быть словарем со статистическим анализом.")
        
        # Проверяем интеграцию с репозиторием через уникальный ID в истории
        history = self.git_inspector.get_commit_history(max_count=5)
        found_commit = any(self.unique_id in commit.get("message", "") for commit in history)
        self.assertTrue(found_commit, "История коммитов должна содержать уникальный ID текущего теста.")


if __name__ == "__main__":
    unittest.main()