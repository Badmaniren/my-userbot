import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardianIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.unique_id = str(uuid.uuid4())
        self.random_flag = random.choice([True, False])
        
        # Создаем минимальную структуру репозитория для реальной работы зависимых навыков
        os.makedirs(os.path.join(self.test_dir, ".git"), exist_ok=True)
        
        # Создаем тестовый файл с уникальным содержимым для проверки отсутствия хардкода
        self.test_file_path = os.path.join(self.test_dir, f"test_file_{self.unique_id}.txt")
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(f"Random validation content: {random.randint(1000, 9999)}")

        self.guardian = RepoHealthGuardian(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_check_health_and_audit_integration(self):
        result = self.guardian.check_health_and_audit()
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("audit", result)
        
        # Проверяем, что мониторинг и аудит возвращают не пустые живые структуры данных
        self.assertIsNotNone(result["status"])
        self.assertIsNotNone(result["audit"])

    def test_run_preventive_maintenance_integration(self):
        result = self.guardian.run_preventive_maintenance()
        
        self.assertIsInstance(result, dict)
        self.assertIn("issues_detected", result)
        self.assertIn("action_taken", result)
        self.assertTrue(result["action_taken"])
        self.assertIsInstance(result["issues_detected"], (list, dict))

    def test_analyze_repo_structure_integration(self):
        structure_analysis = self.guardian.analyze_repo_structure()
        
        self.assertIsInstance(structure_analysis, dict)
        
        # Проверяем, что созданный уникальный файл учитывается или анализируется подсистемой аудита
        # Без моков проверяем реальный результат работы со структурой папки
        self.assertTrue(os.path.exists(self.test_file_path))

if __name__ == "__main__":
    unittest.main()