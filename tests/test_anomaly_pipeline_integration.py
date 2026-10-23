import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_pipeline import start_pipeline
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_filter import start_new

class TestAnomalyPipelineIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.log")
        self.source_id = f"src_{uuid.uuid4().hex[:8]}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.metric_value = random.uniform(10.0, 100.0)
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_anomaly_pipeline_integration(self):
        logger = AnomalyLogger(log_path=self.log_file)
        logger.clear_logs()

        hub = AnomalyAuditHub(
            repo_path=self.test_dir.name,
            log_path=self.log_file,
            threshold=5.0
        )

        telemetry_data = {
            "cpu_load": random.randint(10, 99),
            "memory_usage": random.randint(100, 2048),
            "identifier": str(uuid.uuid4())
        }

        filter_input = {
            "source": self.source_id,
            "severity": self.severity_level,
            "details": f"Random test payload {uuid.uuid4()}",
            "telemetry_snapshot": telemetry_data
        }

        filtered_result = start_new(filter_input)
        self.assertIsNotNone(filtered_result)

        hub.log_anomaly(
            source=self.source_id,
            severity=self.severity_level,
            details=filter_input["details"],
            telemetry_snapshot=telemetry_data
        )

        hub.aggregate_and_report(self.metric_name, self.metric_value)
        report = hub.generate_final_report()

        self.assertIsInstance(report, (dict, str))
        self.assertTrue(os.path.exists(self.log_file))

        logged_anomalies = logger.get_anomalies()
        self.assertGreaterEqual(len(logged_anomalies), 1)

        found = False
        for anomaly in logged_anomalies:
            if anomaly.get("source") == self.source_id:
                found = True
                self.assertEqual(anomaly.get("severity"), self.severity_level)
                break
        
        self.assertTrue(found, "Залогированная аномалия не найдена через AnomalyLogger")

if __name__ == "__main__":
    unittest.main()