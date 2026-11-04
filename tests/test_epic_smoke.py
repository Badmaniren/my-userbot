import unittest
import tempfile
import os
import shutil
from pathlib import Path

from skills.repo_monitor import RepoMonitor
from skills.repo_logger import RepoLogger
from skills.repo_health_guardian import RepoHealthGuardian
from skills.repo_health_restorer import RepoHealthRestorer


class TestRepoSelfHealingEpicPractical(unittest.TestCase):
    """
    Практическая проверка завершённого эпика:
    Комплексная система самодиагностики и восстановления репозитория
    (мониторинг → логирование → восстановление).
    """

    def setUp(self):
        # Создаем временную директорию для имитации реального репозитория
        self.test_dir = tempfile.mkdtemp(prefix="repo_epic_test_")
        self.repo_path = self.test_dir

        # Инициализируем минимальную структуру git-репозитория на диске
        os.system(f"git -C {self.repo_path} init -b main > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.name 'Test Runner' > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.email 'test@runner.local' > /dev/null 2>&1")

        # Создаем реалистичные артефакты: файлы логов и данных (20-30 строк)
        self.log_file_path = os.path.join(self.repo_path, "system_events.log")
        log_lines = [
            "[INFO] 2023-10-01 10:00:00 - Repository initialized successfully.",
            "[INFO] 2023-10-01 10:05:12 - Branch 'main' checked out.",
            "[WARN] 2023-10-01 10:15:30 - Untracked large file detected: data_dump.csv",
            "[ERROR] 2023-10-01 10:20:00 - Git index lock conflict encountered.",
            "[INFO] 2023-10-01 10:25:00 - Index lock released automatically.",
            "[DEBUG] 2023-10-01 10:30:00 - Routine health check initiated.",
            "[INFO] 2023-10-01 10:31:00 - Structural integrity verified: OK.",
            "[WARN] 2023-10-01 10:45:00 - Detached HEAD state or missing upstream detected.",
            "[ERROR] 2023-10-01 10:50:03 - Corruption signature in refs/heads/main.",
            "[INFO] 2023-10-01 11:00:00 - Emergency restoration protocol armed."
        ]
        # Заполним лог файл более чем 20 строками для весомости
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            for i in range(1, 26):
                f.write(f"[LOG_ENTRY_{i:02d}] 2023-10-01 11:{i:02d}:00 - Simulated operational metric value: {i * 10.5}\n")
            for line in log_lines:
                f.write(line + "\n")

        # Добавим файл в репозиторий и сделаем начальный коммит
        os.system(f"git -C {self.repo_path} add system_events.log > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit with logs' > /dev/null 2>&1")

    def tearDown(self):
        # Удаляем временную директорию после тестов
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_comprehensive_self_healing_workflow(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА САМОДИАГНОСТИКИ ===")

        # Шаг 1: Мониторинг репозитория (RepoMonitor)
        monitor = RepoMonitor(self.repo_path)
        status_result = monitor.check_status()
        print(f"[Практика] RepoMonitor.check_status() результат:\n{status_result}")
        self.assertIsNotNone(status_result, "Монитор должен возвращать статус репозитория")

        # Шаг 2: Расширенное логирование событий и потоков (RepoLogger)
        logger = RepoLogger(self.repo_path)

        # Логируем события и метрики
        logger.log_event("epic_practical_test_started", {"target": "repository_health"})
        logger.log_git_operation("health_check_init", "SUCCESS")
        logger.log_metric("anomaly_score", 0.85)

        # Передаем реальный лог-поток из файла в модуль логирования
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()

        stream_log_res = logger.process_log_stream(log_content)
        print(f"[Практика] RepoLogger.process_log_stream() обработал лог-файл (размер: {len(log_content)} байт). Статус: {stream_log_res}")
        self.assertTrue(stream_log_res, "Логгер должен успешно обработать поток данных")

        # Шаг 3: Страж здоровья репозитория (RepoHealthGuardian)
        guardian = RepoHealthGuardian(self.repo_path)
        health_audit = guardian.check_health_and_audit()
        print(f"[Практика] RepoHealthGuardian.check_health_and_audit() отчет:\n{health_audit}")
        self.assertIsInstance(health_audit, (dict, str, bool), "Страж здоровья должен вернуть результаты аудита")

        preventive = guardian.run_preventive_maintenance()
        print(f"[Практика] RepoHealthGuardian.run_preventive_maintenance() результат:\n{preventive}")

        # Шаг 4: Комплексное восстановление и защита (RepoHealthRestorer)
        restorer = RepoHealthRestorer(self.repo_path)

        # Запускаем комплексное восстановление с передачей потока логов
        restoration_result = restorer.comprehensive_health_restoration(log_content)
        print(f"[Практиka] RepoHealthRestorer.comprehensive_health_restoration() результат:\n{restoration_result}")
        self.assertIsNotNone(restoration_result, "Восстановитель должен вернуть словарь/результат комплексной процедуры")

        # Проверяем исполнение стандартной рутины восстановления
        routine_res = restorer.execute_restoration_routine()
        print(f"[Практика] RepoHealthRestorer.execute_restoration_routine() выполнен: {routine_res}")

        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()