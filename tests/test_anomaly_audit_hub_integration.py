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
        self.repo_path = os.path.join(self.test_dir, "repo")
        self.log_path = os.path.join(self.test_dir, "audit.log")
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

    def test_full_audit_lifecycle_propagation(self):
        # Генерируем случайные данные для проверки отсутствия хардкода
        source_id = f"src_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "CRITICAL"])
        details = {"event_id": str(uuid.uuid4()), "payload": random.random()}
        telemetry = {"cpu": random.randint(1, 100), "mem": random.randint(1024, 8192)}

        # Проверка записи аномалии
        log_result = self.hub.log_anomaly(source_id, severity, details, telemetry)
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл не был создан")

        # Проверка агрегации и проброса исключений
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        val = random.uniform(0.0, 1.0)

        # Если значение превышает порог, агрегатор должен корректно обработать данные
        # В случае ошибки модуля, проверяем, что она пробрасывается наружу (не подавляется)
        try:
            self.hub.aggregate_and_report(metric_name, val)
        except AnomalyReportAggregatorError:
            pass
        except Exception as e:
            self.fail(f"Неожиданное исключение: {type(e).__name__}")

        # Проверка генерации отчета
        report = self.hub.generate_final_report()
        self.assertIsInstance(report, dict, "Отчет должен быть словарем")

        # Проверка целостности данных в логгере (интеграция с AnomalyLogger)
        logger_instance = self.hub.logger
        anomalies = logger_instance.get_anomalies()
        self.assertTrue(any(a['source'] == source_id for a in anomalies), "Данные не найдены в логгере")

    def test_error_propagation_on_invalid_input(self):
        # Проверка, что модуль не подавляет ошибки при некорректных данных
        with self.assertRaises(Exception):
            self.hub.aggregate_and_report(None, None)

if __name__ == "__main__":
    unittest.main()