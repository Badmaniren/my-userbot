import unittest
import tempfile
import os
import subprocess
from pathlib import Path
from skills.repo_monitor import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.repo_auto_committer import RepoAutoCommitter


class TestAutoDocumentationPipelineLive(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_path, check=True, capture_output=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_real_conditions(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: КОНВЕЙЕР АВТО-ДОКУМЕНТИРОВАНИЯ ===")

        print("\n[Шаг 1] Создание реалистичных изменений в рабочей директории...")
        file_path = Path(self.repo_path) / "feature_log.txt"

        log_lines = [
            f"2023-10-25 10:00:00 - INFO - Инициализация модуля мониторинга репозитория [запись #{i}]"
            for i in range(1, 26)
        ]
        file_path.write_text("\n".join(log_lines), encoding="utf-8")
        print(f"Создан файл {file_path.name} с {len(log_lines)} строками логов изменений.")

        print("\n[Шаг 2] Проверка модуля repo_monitor...")
        monitor = RepoMonitor(self.repo_path)
        status_output = monitor.check_status()
        print("Результат работы RepoMonitor.check_status():")
        print("-" * 40)
        print(status_output)
        print("-" * 40)
        self.assertTrue(len(status_output) > 0, "RepoMonitor не должен возвращать пустую строку")

        print("\n[Шаг 3] Проверка модуля repo_summarizer...")
        summarizer = RepoSummarizer(self.repo_path)
        summary_output = summarizer.generate_summary()
        print("Сгенерированная сводка (RepoSummarizer.generate_summary()):")
        print("-" * 40)
        print(summary_output)
        print("-" * 40)
        self.assertTrue(isinstance(summary_output, str), "Сводка должна быть строкой")
        self.assertGreater(len(summary_output), 0, "Сводка не должна быть пустой")

        print("\n[Шаг 4] Проверка финального конвейера repo_auto_committer...")
        auto_committer = RepoAutoCommitter(self.repo_path)

        success = auto_committer.process_and_commit()
        print(f"Статус выполнения process_and_commit(): {success}")
        self.assertTrue(success, "Конвейер автокоммита должен успешно завершиться")

        result = subprocess.run(
            ["git", "log", "-n", "1", "--oneline"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        last_commit = result.stdout.strip()
        print(f"Последний коммит в репозитории: {last_commit}")
        self.assertTrue(len(last_commit) > 0, "В репозитории должен появиться зафиксированный коммит")

        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()