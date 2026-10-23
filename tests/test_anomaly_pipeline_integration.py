import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.anomaly_pipeline import anomaly_pipeline_main, start_new
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector


class TestAnomalPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir
        self.threshold = random.uniform(0.5, 0.9)

        self.source_id = f"source_{uuid.uuid4()}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = random.randint(10, 100)
        self.random_details = f"Anomaly test run ID: {uuid.uuid4()}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_anomaly_pipeline_full_integration(self):
        git_insp = GitInspector(repo_path=self.repo_path)
        commits = git_insp.get_history()
        self.assertIsInstance(commits, list)

        logger = AnomalyLogger(log_path=self.log_file)
        logger.clear_logs()
        initial_logs = logger.get_anomalies()
        self.assertEqual(len(initial_logs), 0)

        audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

        telemetry_snapshot = {
            "random_entropy": random.random(),
            "run_uuid": str(uuid.uuid4())
        }

        audit_hub.log_anomaly(
            source=self.source_id,
            severity=self.severity_level,
            details=self.random_details,
            telemetry_snapshot=telemetry_snapshot
        )

        audit_hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        filtered_data = start_new({"metric": self.metric_name, "value": self.metric_value})
        self.assertIsNotNone(filtered_data)

        pipeline_result = anomaly_pipeline_main(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )
        self.assertIsNotNone(pipeline_result)

        stored_anomalies = logger.get_anomalies()
        self.assertGreaterEqual(len(stored_anomalies), 1)

        found_target = False
        for anomaly in stored_anomalies:
            if isinstance(anomaly, dict) and anomaly.get("source") == self.source_id:
                found_target = True
                self.assertEqual(anomaly.get("details"), self.random_details)
                self.assertEqual(anomaly.get("severity"), self.severity_level)
                break
            elif hasattr(anomaly, "source") and anomaly.source == self.source_id:
                found_target = True
                self.assertEqual(anomaly.details, self.random_details)
                self.assertEqual(anomaly.severity, self.severity_level)
                break

        self.assertTrue(found_target, f"Не найдена аномалия с source={self.source_id} в логах.")
        self.assertTrue(os.path.exists(self.log_file), "Файл логов аудита не был создан в процессе интеграционного прогона.")


if __name__ == "__main__":
    unittest.main()