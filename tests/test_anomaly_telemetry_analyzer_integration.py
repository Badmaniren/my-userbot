import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_filter import start_new
from skills.anomaly_telemetry_analyzer import AnomalyTelemetryAnalyzer, AnomalyTelemetryAnalyzerError

class TestAnomalyTelemetryAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.log")
        self.repo_path = self.test_dir.name
        self.threshold = random.uniform(0.5, 0.9)
        self.audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_file, threshold=self.threshold)
        self.anomaly_logger = AnomalyLogger(log_path=self.log_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_telemetry_analyzer_integration_flow(self):
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.randint(1, 10)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(10.0, 100.0)

        telemetry_snapshot = {
            "cpu_load": random.uniform(20.0, 99.9),
            "memory_usage": random.randint(1024, 8192),
            "active_threads": random.randint(5, 50)
        }

        filter_data = {
            "source": source_id,
            "severity": "HIGH",
            "details": f"Test anomaly detected with value {metric_value}",
            "telemetry_snapshot": telemetry_snapshot
        }

        filter_result = start_new(filter_data)

        analyzer = AnomalyTelemetryAnalyzer(
            telemetry_stream=[telemetry_snapshot],
            confidence_threshold=self.threshold
        )
        patterns_result = analyzer.analyze_deep_patterns()
        signal_result = analyzer.extract_hidden_signals(source_id)

        self.assertEqual(patterns_result["status"], "analyzed")
        self.assertEqual(patterns_result["patterns"], 1)
        self.assertEqual(signal_result["signal"], source_id)

        self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=f"Test anomaly detected with value {metric_value}",
            telemetry_snapshot=telemetry_snapshot
        )

        self.audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        final_report = self.audit_hub.generate_final_report()

        logged_anomalies = self.anomaly_logger.get_anomalies()
        structured_report = self.anomaly_logger.get_structured_report()

        self.assertTrue(os.path.exists(self.log_file), "Лог-файл аудита не был создан.")
        self.assertGreaterEqual(len(logged_anomalies), 1, "Аномалия не была зафиксирована в логере.")

        found = False
        for anomaly in logged_anomalies:
            if anomaly.get("source") == source_id:
                found = True
                self.assertEqual(anomaly.get("severity"), severity_level)
                self.assertEqual(anomaly.get("telemetry_snapshot"), telemetry_snapshot)
                break
        self.assertTrue(found, f"Источник аномалии {source_id} не найден в записях логера.")

        self.assertIsNotNone(final_report)
        self.assertIsNotNone(structured_report)
        self.assertIsNotNone(filter_result)

if __name__ == "__main__":
    unittest.main()