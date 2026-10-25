import unittest
import os
import shutil
import uuid
import random
from skills.anomaly_metrics_collector import AnomalyMetricsCollector
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyMetricsCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.repo_path = f"./test_repo_{self.test_id}"
        self.log_path = f"./test_logs_{self.test_id}"

        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)

        self.metric_name = f"metric_{random.randint(1000, 9999)}"
        self.metric_value = random.uniform(10.0, 100.0)
        self.source = f"source_{random.randint(100, 999)}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details = f"Random anomaly detail {uuid.uuid4()}"
        self.telemetry = {"cpu_load": random.randint(1, 100), "memory_usage": random.randint(100, 999)}

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)
        if os.path.exists(self.log_path):
            shutil.rmtree(self.log_path)

    def test_metrics_collector_integration_with_audit_hub(self):
        collector = AnomalyMetricsCollector()
        audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=50.0)
        logger = AnomalyLogger(log_path=self.log_path)

        collected_data = collector.collect(
            metric_name=self.metric_name,
            value=self.metric_value,
            telemetry_snapshot=self.telemetry
        )

        self.assertIsNotNone(collected_data)

        audit_hub.aggregate_and_report(metric_name=self.metric_name, value=self.metric_value)

        logger.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry
        )

        anomalies = logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1)

        found = False
        for anomaly in anomalies:
            if anomaly.get("source") == self.source and anomaly.get("details") == self.details:
                found = True
                break
        self.assertTrue(found, "Logged anomaly with random details was not found in AnomalyLogger")

        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

if __name__ == '__main__':
    unittest.main()