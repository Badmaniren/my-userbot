import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.anomaly_telemetry_collector import (
    AnomalyTelemetryCollector,
    AnomalyTelemetryCollectorError
)
from skills.anomaly_logger import AnomalyLogger


class TestAnomalyTelemetryCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        self.log_path = os.path.join(self.test_dir, "logs", "anomaly.log")
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        self.anomaly_id = str(uuid.uuid4())
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = random.uniform(10.0, 100.0)
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.source = f"service_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_telemetry_collector_aggregation_integration(self):
        log_file = os.path.join(self.test_dir, "logs", "telemetry.log")
        collector = AnomalyTelemetryCollector(log_path=log_file, threshold=50)
        result = collector.aggregate_metrics(self.metric_name, self.metric_value)

        self.assertEqual(result["metric_name"], self.metric_name)
        self.assertEqual(result["value"], self.metric_value)
        self.assertEqual(result["status"], "aggregated")

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(f"{self.metric_name}:{self.metric_value}", content)

    def test_telemetry_collection_and_audit_hub_integration(self):
        logger = AnomalyLogger(log_path=self.log_path)

        collector = AnomalyTelemetryCollector(log_path=os.path.join(self.test_dir, "logs", "collector.log"))

        telemetry_snapshot = {
            "anomaly_id": self.anomaly_id,
            "cpu_load": random.randint(0, 100),
            "memory_usage": random.uniform(1024.0, 8192.0),
            "active_connections": random.randint(1, 500)
        }

        details = {
            "description": f"Integration test anomaly event {self.anomaly_id}",
            "error_code": random.randint(500, 599)
        }

        logger.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        collector_agg = collector.aggregate_metrics(self.metric_name, self.metric_value)
        self.assertEqual(collector_agg["status"], "aggregated")

        final_report = logger.get_structured_report()

        self.assertIsNotNone(final_report)

        anomalies = logger.get_anomalies()

        found = False
        for anomaly in anomalies:
            if anomaly.get("telemetry_snapshot", {}).get("anomaly_id") == self.anomaly_id:
                found = True
                self.assertEqual(anomaly.get("source"), self.source)
                self.assertEqual(anomaly.get("severity"), self.severity)
                break

        self.assertTrue(found, f"Anomaly with ID {self.anomaly_id} was not found in logs via AnomalyLogger.")


if __name__ == "__main__":
    unittest.main()
