import unittest
import uuid
import random
import tempfile
import os
import shutil

from skills.repo_security_scanner import repo_security_scanner
from skills.repo_auditor import repo_auditor
from skills.vulnerability_analyzer import vulnerability_analyzer
from skills.repo_reporter import repo_reporter


class TestRepoSecurityScannerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.unique_marker = f"sec_test_{uuid.uuid4().hex}"
        
        # Создаем файлы в репозитории для реального сканирования
        self.vulnerable_file = os.path.join(self.test_dir, "app.py")
        with open(self.vulnerable_file, "w", encoding="utf-8") as f:
            f.write(f"# {self.unique_marker}\n")
            f.write("import os\n")
            f.write("def run_cmd(user_input):\n")
            f.write("    os.system(user_input)\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_security_scanner_integration(self):
        # Генерируем случайные параметры аудита для исключения хардкода
        scan_id = str(uuid.uuid4())
        severity_threshold = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        # Шаг 1: Запуск аудита репозитория через реальную связанную зависимость
        audit_result = repo_auditor(
            repo_path=self.test_dir,
            audit_id=scan_id
        )
        self.assertIsNotNone(audit_result)

        # Шаг 2: Анализ уязвимостей без моков
        vuln_analysis = vulnerability_analyzer(
            target_path=self.vulnerable_file,
            threshold=severity_threshold
        )
        self.assertIsInstance(vuln_analysis, dict)

        # Шаг 3: Вызов целевого модуля комплексного сканирования
        scanner_payload = {
            "scan_uuid": scan_id,
            "path": self.test_dir,
            "marker": self.unique_marker,
            "severity": severity_threshold
        }
        
        scan_output = repo_security_scanner(scanner_payload)
        
        # Проверяем реальный результат выполнения целевого модуля
        self.assertIsInstance(scan_output, dict)
        self.assertIn("status", scan_output)
        self.assertEqual(scan_output.get("scan_uuid"), scan_id)

        # Шаг 4: Генерация отчета по безопасности для проверки сквозной интеграции
        report_output = repo_reporter(
            data=scan_output,
            format="json"
        )
        self.assertIsNotNone(report_output)


if __name__ == "__main__":
    unittest.main()