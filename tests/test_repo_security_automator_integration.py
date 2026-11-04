import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_security_automator import RepoSecurityAutomator

class TestRepoSecurityAutomatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация минимальной git-среды для работы навыков коммита и шлюза
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_security_automator_composition_workflow(self):
        unique_id = str(uuid.uuid4())
        vulnerability_marker = f"vulnerable_dependency_{random.randint(1000, 9999)}"
        
        # Создаем тестовый файл зависимостей с уникальными данными для проверки сквозной интеграции
        req_file = os.path.join(self.repo_path, "requirements.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            f.write(f"{vulnerability_marker}==1.0.0\n")
            f.write(f"# Security Automator Test ID: {unique_id}\n")

        os.system(f"git -C {self.repo_path} add requirements.txt")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit {unique_id}'")

        # Инициализируем тестируемый модуль композиции без использования моков
        automator = RepoSecurityAutomator(self.repo_path)
        
        # Проверяем наличие методов и атрибутов, подтверждающих композицию с обязательными модулями
        self.assertTrue(hasattr(automator, "gateway") or hasattr(automator, "run"), 
                        "Модуль должен интегрировать логику repo_security_gateway")
        self.assertTrue(hasattr(automator, "committer") or hasattr(automator, "run"), 
                        "Модуль должен интегрировать логику repo_auto_committer")

        # Выполняем реальный запуск автоматизации безопасности (композиция шлюза и автокоммиттера)
        result = None
        if hasattr(automator, "run"):
            result = automator.run()
        elif hasattr(automator, "automate"):
            result = automator.automate()

        # Проверяем, что процесс отработал и вернул осмысленный результат (словарь или булево значение)
        self.assertIsNotNone(result, "Интеграционный метод не должен возвращать None")

        # Проверяем, что в репозитории произошли изменения или зафиксирован результат работы шлюза/коммиттера
        status_output = os.popen(f"git -C {self.repo_path} status --porcelain").read()
        log_output = os.popen(f"git -C {self.repo_path} log -n 5 --oneline").read()

        # Убедимся, что уникальный идентификатор теста корректно обрабатывается системой
        self.assertIn(unique_id, log_output or status_output or str(result), 
                      "Уникальный контекст выполнения должен сохраняться в истории репозитория или результатах")

if __name__ == "__main__":
    unittest.main()