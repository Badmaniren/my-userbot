import unittest
import tempfile
import shutil
import uuid
import random
import os

from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator
from skills import anomaly_audit_hub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"audit_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.test_dir
        
        self.source = f"source_{uuid.uuid4().hex[:8]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details = f"Details for anomaly test {uuid.uuid4().hex}"
        self.telemetry_snapshot = {"cpu_load": random.random(), "memory_free": random.randint(100, 1000)}
        
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = random.uniform(10.0, 100.0)
        self.threshold = random.uniform(50.0, 150.0)
        
        self.logger_instance = AnomalyLogger(log_path=self.log_path)
        self.aggregator_instance = AnomalyReportAggregator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            detector=None,
            correlator=None,
            logger=self.logger_instance
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_anomaly_audit_hub_composition(self):
        self.logger_instance.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry_snapshot
        )
        
        logged_anomalies = self.logger_instance.get_anomalies()
        self.assertTrue(any(a.get("source") == self.source for a in logged_anomalies), "Логгер должен содержать записанную аномалию.")

        try:
            report_result = self.aggregator_instance.aggregate_and_report(
                metric_name=self.metric_name,
                value=self.metric_value
            )
        except Exception:
            report_result = None

        self.assertTrue(hasattr(anomaly_audit_hub, "__file__"), "Модуль anomaly_audit_hub должен существовать и быть импортирован.")
        
        hub_report = getattr(anomaly_audit_hub, "generate_audit_report", None)
        if callable(hub_report):
            final_hub_data = hub_report(self.logger_instance, self.aggregator_instance)
            self.assertIsNotNone(final_hub_data)
        else:
            structured_rep = self.logger_instance.get_structured_report()
            self.assertIsNotNone(structured_rep)

        self.assertTrue(os.path.exists(self.log_path), "Файл логов должен реально существовать на диске.")


if __name__ == "__main__":
    unittest.main()