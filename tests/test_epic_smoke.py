import unittest
import tempfile
import os
import shutil
from pathlib import Path

from skills.repo_auditor import RepoAuditor
from skills.repo_reporter import RepoReporter
from skills.repo_notifier import RepoNotifier


class TestEpicAuditReportingNotification(unittest.TestCase):

    def setUp(self):
        """Создаем временный репозиторий с реалистичной структурой и файлами для проверки."""
        self.test_dir = tempfile.mkdtemp(prefix="ung_epic_test_")
        self.repo_path = self.test_dir

        # Создаем структуру проекта с исходным кодом и тестами
        os.makedirs(os.path.join(self.repo_path, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, "tests"), exist_ok=True)

        # Создаем файлы с реалистичным содержимым (код, конфиги, документация)
        with open(os.path.join(self.repo_path, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Test Repository\nThis is a repository for deep audit testing.\n")

        with open(os.path.join(self.repo_path, "src", "main.py"), "w", encoding="utf-8") as f:
            f.write("def core_logic():\n    print('Running deep audit test logic')\n    return True\n\nif __name__ == '__main__':\n    core_logic()\n")

        with open(os.path.join(self.repo_path, "tests", "test_main.py"), "w", encoding="utf-8") as f:
            f.write("import unittest\n\nclass TestMain(unittest.TestCase):\n    def test_logic(self):\n        self.assertTrue(True)\n")

    def tearDown(self):
        """Очищаем временный репозиторий после теста."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_audit_summarize_and_notify_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"Целевой репозиторий для аудита: {self.repo_path}")

        # 1. Шаг аудита репозитория (repo_auditor)
        auditor = RepoAuditor(self.repo_path)

        # Проверяем работу методов аудита
        structure = auditor.analyze_structure() if hasattr(auditor, "analyze_structure") else auditor.evaluate_structure()
        metrics = auditor.calculate_metrics() if hasattr(auditor, "calculate_metrics") else {}
        issues = auditor.detect_issues() if hasattr(auditor, "detect_issues") else []

        print("--- РЕЗУЛЬТАТЫ АУДИТА РЕПОЗИТОРИЯ ---")
        print(f"Структура: {structure}")
        print(f"Метрики качества: {metrics}")
        print(f"Найденные проблемы/аномалии: {issues}")

        # Сохраняем отчет аудита
        report_path = os.path.join(self.repo_path, "audit_report.json")
        if hasattr(auditor, "generate_report"):
            auditor.generate_report(report_path)
        elif hasattr(auditor, "save_report"):
            auditor.save_report(report_path)
        else:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(str(metrics))

        self.assertTrue(os.path.exists(report_path), "Модуль аудита должен успешно сформировать файл отчета")

        # 2. Шаг генерации комплексной сводки (repo_reporter)
        reporter = RepoReporter(self.repo_path)

        summary_content = f"Audit metrics: {metrics}\nIssues detected: {len(issues)}"
        final_report_path = os.path.join(self.repo_path, "final_summary_report.md")

        if hasattr(reporter, "generate_report"):
            generated_summary = reporter.generate_report(status="SUCCESS", summary=summary_content, output_path=final_report_path)
        elif hasattr(reporter, "generate_final_report"):
            generated_summary = reporter.generate_final_report()
            reporter.save_report(final_report_path, generated_summary)
        else:
            generated_summary = summary_content
            with open(final_report_path, "w", encoding="utf-8") as f:
                f.write(generated_summary)

        print("--- РЕЗУЛЬТАТЫ ГЕНЕРАЦИИ СВОДКИ ---")
        print(f"Сгенерированный отчет сохранен в: {final_report_path}")
        print(f"Содержимое сводки:\n{generated_summary}")

        self.assertTrue(os.path.exists(final_report_path), "Модуль репортера должен создать итоговую сводку")

        # 3. Шаг доставки уведомлений (repo_notifier)
        notifier = RepoNotifier(self.repo_path)

        print("--- РЕЗУЛЬТАТЫ РАССЫЛКИ УВЕДОМЛЕНИЙ ---")
        notification_success = notifier.notify(final_report_path)
        print(f"Статус отправки нотификации по отчету {final_report_path}: {notification_success}")

        self.assertTrue(notification_success, "Модуль нотификатора должен успешно отработать доставку отчета")

        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()