import unittest
import tempfile
import os
import json
from pathlib import Path

from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_notifier import RepoNotifier
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestExternalMonitoringEcosystem(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        # Создаем реалистичные данные на диске для проверки работы модулей
        self.log_file_path = os.path.join(self.repo_path, "system_metrics.json")
        self.report_file_path = os.path.join(self.repo_path, "health_report.json")

        # Генерация 20-30 строк реалистичных данных телеметрии репозитория
        self.mock_stream_data = {
            "timestamp": "2023-10-25T10:00:00Z",
            "repository": "ung-core-system",
            "metrics": [
                {"metric_key": "uncommitted_changes", "metric_value": 3, "status": "warning"},
                {"metric_key": "branch_count", "metric_value": 12, "status": "ok"},
                {"metric_key": "open_issues", "metric_value": 5, "status": "ok"},
                {"metric_key": "disk_usage_mb", "metric_value": 450, "status": "ok"},
                {"metric_key": "pending_security_patches", "metric_value": 2, "status": "warning"},
                {"metric_key": "last_commit_age_hours", "metric_value": 14, "status": "ok"},
                {"metric_key": "failed_builds_count", "metric_value": 0, "status": "ok"},
                {"metric_key": "active_contributors", "metric_value": 8, "status": "ok"}
            ],
            "system_logs": [
                "INFO: Repository structure checked successfully.",
                "WARNING: 3 uncommitted changes detected in working directory.",
                "INFO: Auto-committer standby mode active.",
                "WARNING: 2 pending security patches require attention.",
                "INFO: Backup routine completed without errors.",
                "INFO: Health dashboard aggregation started.",
                "INFO: Metrics stream processed successfully."
            ]
        }

        with open(self.log_file_path, "w", encoding="utf-8") as f:
            json.dump(self.mock_stream_data, f, indent=4)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_monitoring_ecosystem_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"Рабочая директория репозитория: {self.repo_path}")

        # Шаг 1: repo_health_dashboard (Агрегация метрик и визуализация состояния)
        print("\n[Шаг 1] Инициализация и запуск RepoHealthDashboard...")
        dashboard = RepoHealthDashboard(self.repo_path)

        # Обрабатываем поток данных из файла
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            stream_content = json.load(f)

        dashboard_result = dashboard.process_stream(stream_content)
        print(f"Результат обработки потока дашбордом: {dashboard_result}")

        # Экспортируем дашборд для проверки генерации отчета
        export_success = dashboard.export_dashboard(self.report_file_path)
        print(f"Статус экспорт дашборда в файл ({self.report_file_path}): {export_success}")
        self.assertTrue(export_success, "Дашборд должен успешно экспортировать данные в файл отчета")
        self.assertTrue(os.path.exists(self.report_file_path), "Файл отчета дашборда должен существовать на диске")

        # Шаг 2: repo_notifier (Связь с уведомлениями)
        print("\n[Шаг 2] Инициализация и запуск RepoNotifier...")
        notifier = RepoNotifier(self.repo_path)

        # Отправляем уведомление по сгенерированному отчету
        notification_success = notifier.notify(self.report_file_path)
        print(f"Статус отправки уведомления внешним потребителям: {notification_success}")
        self.assertTrue(notification_success, "Модуль уведомлений должен успешно обработать отчет")

        # Шаг 3: repo_health_dispatcher (Единый диспетчер рассылки отчетов)
        print("\n[Шаг 3] Инициализация и запуск RepoHealthDispatcher...")
        dispatcher = RepoHealthDispatcher(self.repo_path)

        dispatch_success = dispatcher.process_stream_and_dispatch(stream_content, self.report_file_path)
        print(f"Статус комплексного диспетчирования (аналитика + уведомления): {dispatch_success}")
        self.assertTrue(dispatch_success, "Диспетчер должен успешно связать аналитику и рассылку")

        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()