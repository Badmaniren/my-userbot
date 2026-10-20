import unittest
import os
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
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

    def test_full_audit_lifecycle_integration(self):
        # Генерируем случайные данные для проверки отсутствия хардкода
        source_id = f"src_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(100, 999), "msg": "integration_test"}
        telemetry = {"cpu": random.random(), "mem": random.random()}

        # 1. Проверка логирования
        log_result = self.hub.log_anomaly(source_id, severity, details, telemetry)
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл не был создан")

        # 2. Проверка агрегации
        metric_name = f"metric_{uuid.uuid4().hex[:5]}"
        value = random.uniform(0.0, 1.0)

        # Если значение превышает порог, агрегатор должен зафиксировать это
        self.hub.aggregate_and_report(metric_name, value)

        # 3. Проверка генерации отчета
        report = self.hub.generate_final_report()
        self.assertIsInstance(report, dict, "Отчет должен быть словарем")

        # Проверяем, что данные попали в отчет (интеграция с AnomalyLogger)
        found = False
        for entry in report.get("anomalies", []):
            if entry.get("source") == source_id:
                found = True
                self.assertEqual(entry.get("severity"), severity)

        self.assertTrue(found, "Данные не были найдены в итоговом отчете после агрегации")

    def test_exception_propagation(self):
        # Проверка того, что ошибки не подавляются (согласно требованиям эпика)
        # Передаем некорректный тип данных, чтобы спровоцировать ошибку в агрегаторе
        with self.assertRaises((TypeError, AnomalyReportAggregatorError)):
            self.hub.aggregate_and_report("invalid_metric", "not_a_float")

if __name__ == "__main__":
    unittest.main()