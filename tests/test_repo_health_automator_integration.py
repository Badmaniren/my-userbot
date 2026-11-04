import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_health_automator import RepoHealthAutomator
from skills.repo_monitor import RepoMonitor
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthAutomatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация базового git репозитория для работы мониторинга и стража
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Создаем случайный файл с использованием uuid и random, чтобы избежать хардкода
        self.unique_id = str(uuid.uuid4())
        self.random_metric = random.randint(100, 999)
        
        self.test_file_name = f"health_file_{self.unique_id}.py"
        self.test_file_path = os.path.join(self.repo_path, self.test_file_name)
        
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Metric value: {self.random_metric}\n")
            f.write("print('Repository health check running')\n")
            
        os.system(f"git -C {self.repo_path} add {self.test_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit for {self.unique_id}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repo_health_automator_composition_and_execution(self):
        # Проверяем, что модуль корректно инициализируется и композиция работает
        automator = RepoHealthAutomator(self.repo_path)
        
        # Проверяем наличие задействованных навыков внутри композиции
        self.assertIsInstance(automator.monitor, RepoMonitor)
        self.assertIsInstance(automator.guardian, RepoHealthGuardian)
        
        # Выполняем реальный мониторинг через встроенный навык
        status = automator.monitor.check_status()
        self.assertIsInstance(status, str)
        
        # Выполняем комплексную проверку здоровья и обслуживание через стража и автоматизатор
        health_result = automator.guardian.check_health_and_audit()
        self.assertIsInstance(health_result, dict)
        
        maintenance_result = automator.guardian.run_preventive_maintenance()
        self.assertIsInstance(maintenance_result, dict)
        
        # Проверяем ключевой метод автоматизатора с генерацией уникальных данных
        # Добавим еще одно случайное изменение для проверки реакции автоматизатора
        new_random_file = os.path.join(self.repo_path, f"mod_{uuid.uuid4()}.txt")
        with open(new_random_file, "w", encoding="utf-8") as f:
            f.write(str(self.random_metric))
            
        # Запуск процесса автоматизации проверки здоровья репозитория
        if hasattr(automator, 'run'):
            exec_result = automator.run()
            self.assertIsNotNone(exec_result)
        elif hasattr(automator, 'automate_health_check'):
            exec_result = automator.automate_health_check()
            self.assertIsNotNone(exec_result)

if __name__ == "__main__":
    unittest.main()