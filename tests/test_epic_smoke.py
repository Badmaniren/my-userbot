import unittest
import tempfile
import os
import json
from pathlib import Path

from skills.repo_auditor import RepoAuditor
from skills.repo_health_automator import RepoHealthAutomator
from skills.repo_health_optimizer import RepoHealthOptimizer
from skills.vulnerability_analyzer import VulnerabilityAnalyzer
from skills.git_committer import GitCommitter


class TestEpicSelfHealingEvolution(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        self.reqs_path = os.path.join(self.repo_path, "requirements.txt")
        with open(self.reqs_path, "w", encoding="utf-8") as f:
            f.write("requests==2.25.0\n")
            f.write("flask==1.1.2\n")
            f.write("urllib3<1.26.0\n")
            f.write("jinja2>=2.10\n")

        self.src_dir = os.path.join(self.repo_path, "src")
        os.makedirs(self.src_dir, exist_ok=True)
        self.main_path = os.path.join(self.src_dir, "main.py")

        log_lines = [
            "# Application Runtime Log\n",
            "INFO: Initializing core modules\n",
            "WARN: Deprecated configuration detected in settings.yaml\n",
            "ERROR: Connection timeout on port 5432 (retry 1/3)\n",
            "INFO: Database reconnected successfully\n",
            "WARN: High memory usage: 84% utilized\n",
            "ERROR: Unhandled exception in worker thread: NullReference\n",
            "INFO: Self-healing routine triggered automatically\n",
            "INFO: Routine completed, system stable\n"
        ] * 3

        self.log_path = os.path.join(self.repo_path, "system_runtime.log")
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.writelines(log_lines)

        with open(self.main_path, "w", encoding="utf-8") as f:
            f.write("import requests\nimport flask\n\nprint('System running...')\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_evolution_pipeline_real_conditions(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"Рабочая директория репозитория: {self.repo_path}")

        print("\n[Шаг 1] Запуск аудита репозитория (RepoAuditor)...")
        auditor = RepoAuditor(self.repo_path)
        audit_metrics = auditor.calculate_metrics()
        audit_issues = auditor.detect_issues()

        print(f" -> Рассчитанные метрики: {audit_metrics}")
        print(f" -> Обнаруженные проблемы структуры/кода: {audit_issues}")
        self.assertIsInstance(audit_metrics, dict)
        self.assertIsInstance(audit_issues, list)

        print("\n[Шаг 2] Анализ уязвимостей зависимостей (VulnerabilityAnalyzer)...")
        vuln_analyzer = VulnerabilityAnalyzer(self.repo_path)
        vuln_result = vuln_analyzer.run()
        print(f" -> Результаты сканирования уязвимостей: {json.dumps(vuln_result, indent=2, ensure_ascii=False)}")
        self.assertIsInstance(vuln_result, dict)

        print("\n[Шаг 3] Обработка потока логов через автоматоро здоровье (RepoHealthAutomator)...")
        automator = RepoHealthAutomator(self.repo_path)

        with open(self.log_path, "r", encoding="utf-8") as stream_file:
            automation_result = automator.process_stream_and_automate(stream_file)

        print(f" -> Отчет о работе автоматизации здоровья: {json.dumps(automation_result, indent=2, ensure_ascii=False)}")
        self.assertIsInstance(automation_result, dict)

        print("\n[Шаг 4] Комплексная оптимизация репозитория (RepoHealthOptimizer)...")
        optimizer = RepoHealthOptimizer(self.repo_path)
        optimization_result = optimizer.optimize_repository()

        print(f" -> Итог комплексной оптимизации: {json.dumps(optimization_result, indent=2, ensure_ascii=False)}")
        self.assertIsInstance(optimization_result, dict)

        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()