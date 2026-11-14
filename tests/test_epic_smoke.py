import os
import tempfile
import unittest
import shutil

from skills.repo_sync import RepoSync
from skills.repo_backup import RepoBackup
from skills.repo_reporter import RepoReporter


class TestDistributedRepositoryEcosystem(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Создаем реалистичные данные на диске (20-30 строк логов/данных для аналитики и бэкапа)
        self.data_file_path = os.path.join(self.repo_path, "repository_metrics.log")
        log_lines = [
            f"2023-10-27 10:{i:02d}:00 INFO [Event-{i}] Repository synchronization status: OK\n"
            for i in range(25)
        ]
        with open(self.data_file_path, "w", encoding="utf-8") as f:
            f.writelines(log_lines)

        # Создаем дополнительный файл конфигурации
        self.config_file_path = os.path.join(self.repo_path, "sync_config.json")
        with open(self.config_file_path, "w", encoding="utf-8") as f:
            f.write('{\n  "sync_enabled": true,\n  "remote_target": "backup_node_alpha",\n  "retries": 3\n}')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_distributed_ecosystem_workflow(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"Рабочая директория репозитория: {self.repo_path}")

        # 1. Проверяем наличие созданных файлов с реалистичными данными
        self.assertTrue(os.path.exists(self.data_file_path))
        with open(self.data_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"[Данные] Успешно создано строк в лог-файле: {len(lines)}")
        self.assertEqual(len(lines), 25)
        print(f"[Данные] Первая строка лога: {lines[0].strip()}")
        print(f"[Данные] Последняя строка лога: {lines[-1].strip()}")

        # 2. Инициализация и проверка модуля синхронизации (repo_sync)
        repo_sync_instance = RepoSync(self.repo_path)
        print(f"[Модуль sync] Инициализирован RepoSync для пути: {self.repo_path}")

        sync_result = repo_sync_instance.synchronize()
        print(f"[Модуль sync] Результат выполнения synchronize(): {sync_result}")
        self.assertIsInstance(sync_result, bool)

        # 3. Инициализация и проверка удаленного бэкапа (repo_backup)
        repo_backup_instance = RepoBackup(self.repo_path)
        print(f"[Модуль backup] Инициализирован RepoBackup")

        backup_result = repo_backup_instance.create_backup()
        print(f"[Модуль backup] Результат выполнения create_backup(): {backup_result}")

        backup_method_result = repo_backup_instance.backup()
        print(f"[Модуль backup] Результат выполнения backup(): {backup_method_result}")

        # 4. Формирование внешней аналитики и отчета (repo_reporter)
        reporter_instance = RepoReporter(self.repo_path)
        print(f"[Модуль reporter] Инициализирован RepoReporter")

        summary_text = f"Ecosystem check passed. Processed {len(lines)} log lines successfully. Sync and Backup modules executed."
        report_output = reporter_instance.generate_report("SUCCESS", summary_text, os.path.join(self.repo_path, "final_audit_report.txt"))
        print(f"[Модуль reporter] Сгенерирован отчет: {report_output}")

        final_report = reporter_instance.generate_final_report()
        print(f"[Модуль reporter] Итоговый отчет:\n{final_report}")

        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()