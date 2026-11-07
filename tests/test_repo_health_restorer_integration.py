import unittest
import os
import shutil
import uuid
import tempfile
from io import BytesIO
from skills.repo_health_restorer import RepoHealthRestorer

class TestRepoHealthRestorerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, f"repo_{uuid.uuid4().hex}")
        os.makedirs(self.repo_path)
        
        # Инициализация тестируемого модуля
        self.restorer = RepoHealthRestorer(self.repo_path)
        
        # Создаем фиктивный файл для имитации состояния репозитория
        self.dummy_file = os.path.join(self.repo_path, "test_data.txt")
        with open(self.dummy_file, "w") as f:
            f.write(f"data_{uuid.uuid4().hex}")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_comprehensive_health_restoration_integration(self):
        """
        Интеграционный тест: проверяет взаимодействие RepoHealthRestorer с 
        RepoHealthDiagnostic и RepoRecovery без использования моков.
        """
        # Генерируем случайный поток данных для восстановления
        random_content = f"recovery_payload_{uuid.uuid4().hex}"
        stream = BytesIO(random_content.encode("utf-8"))
        
        # Выполняем комплексное восстановление
        result = self.restorer.comprehensive_health_restoration(stream)
        
        # Проверяем структуру ответа
        self.assertIn("restored", result)
        self.assertIn("structure_analysis", result)
        
        # Проверяем, что восстановление вернуло булево значение (успех)
        self.assertTrue(result["restored"])
        
        # Проверяем, что диагностика вернула данные (словарь)
        self.assertIsInstance(result["structure_analysis"], dict)
        self.assertGreater(len(result["structure_analysis"]), 0)

    def test_execute_restoration_routine_integration(self):
        """
        Интеграционный тест: проверяет цепочку вызовов check_health_and_audit 
        и recover_repository.
        """
        # Выполняем рутину восстановления
        status = self.restorer.execute_restoration_routine()
        
        # Проверяем, что процесс завершился успешно
        self.assertTrue(status)

    def test_restore_and_protect_integration(self):
        """
        Интеграционный тест: проверяет объединение функционала защиты и восстановления.
        """
        report = self.restorer.restore_and_protect()
        
        # Проверяем наличие ключей в отчете
        self.assertIn("recovery_status", report)
        self.assertIn("maintenance_report", report)
        
        # Проверяем типы данных
        self.assertTrue(report["recovery_status"])
        self.assertIsInstance(report["maintenance_report"], dict)

if __name__ == "__main__":
    unittest.main()