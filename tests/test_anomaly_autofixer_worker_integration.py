import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_autofixer_worker import autofix_anomaly
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.git_inspector import GitInspector

class TestAnomalyAutofixerWorkerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, "audit.log")
        
        # Инициализируем реальные компоненты без моков согласно архитектуре
        self.audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=0.5)
        self.git_inspector = GitInspector(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_autofix_anomaly_integration(self):
        # Генерируем уникальные случайные данные для исключения хардкода
        anomaly_id = f"anomaly-{uuid.uuid4()}"
        source_name = f"service-{random.randint(1000, 9999)}"
        severity_level = random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        
        telemetry_data = {
            "metric": f"cpu_load_{random.randint(1, 100)}",
            "value": random.uniform(85.0, 99.9),
            "random_token": str(uuid.uuid4())
        }
        
        details_text = f"Spike detected in {anomaly_id} with token {telemetry_data['random_token']}"

        # Шаг 1: Фиксируем аномалию через аудиторский хаб (реальная интеграция)
        self.audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot=telemetry_data
        )

        # Шаг 2: Вызываем тестируемый модуль автоматического применения исправления
        fix_result = autofix_anomaly(
            anomaly_id=anomaly_id,
            source=source_name,
            repo_path=self.repo_path,
            telemetry=telemetry_data
        )

        # Шаг 3: Проверяем реальные изменения, возвращаемые воркером
        self.assertIsInstance(fix_result, dict)
        self.assertIn("status", fix_result)
        self.assertEqual(fix_result.get("anomaly_id"), anomaly_id)
        
        # Убеждаемся, что воркер зафиксировал успешное применение исправления
        self.assertEqual(fix_result["status"], "applied")
        
        # Шаг 4: Проверяем побочные эффекты на уровне репозитория через GitInspector
        repo_analysis = self.git_inspector.analyze_repository()
        self.assertIsNotNone(repo_analysis)

        # Шаг 5: Проверяем генерацию финального отчета через AnomalyAuditHub
        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)
        
        # Убеждаемся, что данные случайно сгенерированной аномалии попали в аудит
        self.assertTrue(os.path.exists(self.log_path))
        with open(self.log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(anomaly_id, log_content)
            self.assertIn(telemetry_data["random_token"], log_content)

if __name__ == "__main__":
    unittest.main()