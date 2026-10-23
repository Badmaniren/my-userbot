import unittest
import uuid
import random
import tempfile
import os

from skills.anomaly_pipeline import anomaly_pipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector
from skills.anomaly_filter import start_new

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"test_log_{uuid.uuid4().hex}.json")
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = random.uniform(1.0, 100.0)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_pipeline_integration_flow(self):
        source_id = f"source_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Integration test anomaly details {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.randint(10, 99), "memory_usage": random.randint(20, 90)}

        audit_hub = AnomalyAuditHub(
            repo_path=self.test_dir.name,
            log_path=self.log_file,
            threshold=random.uniform(50.0, 90.0)
        )

        audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        audit_hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        logger = AnomalyLogger(log_path=self.log_file)
        logged_anomalies = logger.get_anomalies()

        found = False
        for anomaly in logged_anomalies:
            if anomaly.get("source") == source_id and anomaly.get("details") == details_msg:
                found = True
                break
        self.assertTrue(found, "Logged anomaly should be retrievable via AnomalyLogger.")

        filter_input_data = {
            "source": f"source_{uuid.uuid4().hex[:6]}",
            "severity": "HIGH",
            "details": f"details_{uuid.uuid4().hex[:6]}",
            "telemetry_snapshot": {}
        }
        filtered_result = start_new(filter_input_data)
        self.assertIsNotNone(filtered_result)

        git_inspector = GitInspector(repo_path=self.test_dir.name)
        history = git_inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)

        pipeline_result = anomaly_pipeline()
        self.assertIsNotNone(pipeline_result)
