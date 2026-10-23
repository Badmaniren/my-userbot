import unittest
import os
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        self.log_path = os.path.join(self.test_dir, "audit.log")
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path, exist_ok=True)

        self.threshold = random.uniform(0.1, 0.9)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_anomaly_lifecycle_integration(self):
        # Генерируем случайные данные для теста
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(100, 999), "msg": "test_anomaly"}
        telemetry = {"cpu_load": random.random(), "mem_usage": random.random()}

        # 1. Проверка логирования
        log_result = self.hub.log_anomaly(source_id, severity, details, telemetry)
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл не был создан")

        # 2. Проверка агрегации
        metric_name = f"metric_{uuid.uuid4().hex[:5]}"
        val = random.uniform(0.0, 1.0)
        agg_result = self.hub.aggregate_and_report(metric_name, val)

        # 3. Проверка генерации отчета
        final_report = self.hub.generate_final_report()

        # Валидация состояния
        self.assertIsNotNone(final_report, "Отчет не был сгенерирован")
        self.assertIn(metric_name, str(final_report), "Метрика отсутствует в финальном отчете")

        # Проверка содержимого логов (прямое чтение файла)
        with open(self.log_path, 'r') as f:
            content = f.read()
            self.assertIn(source_id, content)
            self.assertIn(severity, content)

    def test_threshold_logic_integration(self):
        # Проверка влияния порога на агрегацию
        metric_name = "test_threshold_metric"
        # Значение выше порога должно триггерить логику
        val = self.threshold + 0.1

        result = self.hub.aggregate_and_report(metric_name, val)
        report = self.hub.generate_final_report()

        self.assertIsNotNone(report)

if __name__ == '__main__':
    unittest.main()