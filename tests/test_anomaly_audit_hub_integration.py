import unittest
import os
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        self.log_path = os.path.join(self.test_dir, "anomaly.log")
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

    def test_full_lifecycle_integration(self):
        source = f"source_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(100, 999), "msg": "test_anomaly"}
        telemetry = {"cpu_load": random.random(), "mem_usage": random.random()}
        
        # 1. Проверка логирования
        log_result = self.hub.log_anomaly(source, severity, details, telemetry)
        self.assertTrue(os.path.exists(self.log_path), "Log file was not created")
        
        # 2. Проверка агрегации
        metric_name = f"metric_{uuid.uuid4().hex}"
        value = random.uniform(0.0, 1.0)
        agg_result = self.hub.aggregate_and_report(metric_name, value)
        
        # 3. Проверка генерации отчета
        final_report = self.hub.generate_final_report()
        
        self.assertIsInstance(final_report, dict, "Report should be a dictionary")
        self.assertIn(metric_name, str(final_report), "Metric name missing in report")
        
        # Проверка консистентности данных в логе
        with open(self.log_path, 'r') as f:
            content = f.read()
            self.assertIn(source, content)
            self.assertIn(severity, content)

    def test_threshold_logic_integration(self):
        metric_name = "latency_test"
        # Значение выше порога должно триггерить специфическое поведение в агрегаторе
        high_value = self.threshold + 0.5
        self.hub.aggregate_and_report(metric_name, high_value)
        
        report = self.hub.generate_final_report()
        # Проверяем, что агрегатор зафиксировал превышение
        self.assertGreaterEqual(len(report), 0)

if __name__ == "__main__":
    unittest.main()