import unittest
import tempfile
import shutil
import uuid
import random
import os

from skills.anomaly_report_aggregator import AnomalyReportAggregator
from skills.anomaly_correlator import AnomalyCorrelator
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyReportAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"anomalies_{uuid.uuid4().hex}.json")
        self.repo_path = self.test_dir

        self.threshold = round(random.uniform(0.5, 0.9), 2)
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(10.0, 100.0), 2)
        
        self.source = f"source_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.details = f"Details for anomaly test {uuid.uuid4().hex}"
        self.telemetry_snapshot = {"cpu": random.randint(10, 99), "mem": random.randint(20, 90)}

        self.logger = AnomalyLogger(log_path=self.log_path)
        self.correlator = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            detector=None,
            logger=self.logger
        )
        
        self.aggregator = AnomalyReportAggregator(
            correlator=self.correlator,
            logger=self.logger
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_aggregator_real_composition_flow(self):
        self.logger.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry_snapshot
        )

        correlation_result = self.correlator.correlate_metric(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        report = self.aggregator.generate_final_report()

        self.assertTrue(os.path.exists(self.log_path), "Log file must be created by AnomalyLogger via composition.")
        
        logged_anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(logged_anomalies), 1, "At least one anomaly should be logged.")
        
        found_target = False
        for anomaly in logged_anomalies:
            if anomaly.get("details") == self.details:
                found_target = True
                self.assertEqual(anomaly.get("source"), self.source)
                self.assertEqual(anomaly.get("severity"), self.severity)
                self.assertEqual(anomaly.get("telemetry_snapshot"), self.telemetry_snapshot)
                break
        
        self.assertTrue(found_target, "The specifically injected anomaly details must be retrievable from the logger.")
        self.assertIsNotNone(report, "Aggregator must produce a non-null final report.")

if __name__ == "__main__":
    unittest.main()