import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_recovery import RepoRecovery
from skills.repo_backup import RepoBackup
from skills.repo_logger import RepoLogger

class TestRepoRecoveryIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Инициализируем git репозиторий в временной директории
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Architect Test'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")
        
        # Создаем начальный файл и коммитим, чтобы репозиторий не был пустым
        self.initial_file = os.path.join(self.test_dir, "init.txt")
        with open(self.initial_file, "w") as f:
            f.write("initial content")
        os.system(f"git -C {self.test_dir} add . && git -C {self.test_dir} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_recovery_composition_and_logging(self):
        # Генерируем уникальные случайные данные для проверки сквозной интеграции
        unique_id = str(uuid.uuid4())
        metric_key = f"recovery_metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.randint(100, 999)
        
        # Создаем повреждение / вносим изменения, которые нужно обработать
        target_file = os.path.join(self.test_dir, f"data_{unique_id}.txt")
        file_content = f"Random payload data: {uuid.uuid4()}"
        with open(target_file, "w") as f:
            f.write(file_content)

        # Вызываем тестируемый модуль RepoRecovery (композиция repo_backup и repo_logger)
        recovery = RepoRecovery(self.test_dir)
        
        # Проверяем наличие методов и что модуль действительно использует подмодули без моков
        self.assertIsInstance(recovery.backup_handler, RepoBackup)
        self.assertIsInstance(recovery.logger_handler, RepoLogger)

        # Выполняем операцию восстановления/бэкапа через интеграционный метод
        recovery_result = recovery.recover_repository()
        self.assertTrue(recovery_result, "RepoRecovery должен успешно выполнить процесс восстановления/бэкапа")

        # Проверяем, что логгер реально записал событие через реальный repo_logger
        log_event_status = recovery.logger_handler.log_event("RECOVERY_EXECUTED", f"ID: {unique_id}")
        self.assertTrue(log_event_status)

        # Проверяем метрику
        recovery.logger_handler.log_metric(metric_key, metric_value)

        # Проверяем, что резервная копия физически создалась (проверяем функциональность repo_backup)
        backup_status = recovery.backup_handler.create_backup()
        self.assertTrue(backup_status)

        # Дополнительная проверка через git статус или наличие файлов
        self.assertTrue(os.path.exists(target_file))
        with open(target_file, "r") as f:
            read_data = f.read()
        self.assertEqual(read_data, file_content)

if __name__ == "__main__":
    unittest.main()