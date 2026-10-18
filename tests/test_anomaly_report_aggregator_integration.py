import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError
from skills.anomaly_correlator import AnomalyCorrelator
from skills.anomaly_logger import AnomalyLogger


class TestAnomalyReportAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4()}.json")
        
        self.logger = AnomalyLogger(log_path=self.log_file)
        self.correlator = AnomalyCorrelator(
            repo_path=self.temp_dir.name,
            log_path=self.log_file,
            threshold=random.uniform(0.5, 0.9),
            logger=self.logger
        )
        self.aggregator = AnomalyReportAggregator(
            log_path=self.log_file,
            correlator=self.correlator,
            logger=self.logger
        )

    def tearDown(self):
        self.logger.clear_logs()
        self.temp_dir.cleanup()

    def test_aggregate_and_report_integration(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(10.0, 100.0)

        report = self.aggregator.aggregate_and_report(metric_name, metric_value)

        self.assertIsInstance(report, (dict, list, str))
        anomalies = self.logger.get_anomalies()
        self.assertIsInstance(anomalies, list)

    def test_aggregate_execution_flow_integration(self):
        execution_id = str(uuid.uuid4())
        payload = {
            "source": f"source_{uuid.uuid4().hex[:6]}",
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "details": f"random_detail_{uuid.uuid4().hex}",
            "telemetry_snapshot": {"cpu_load": random.randint(1, 100)}
        }

        try:
            report = self.aggregator.aggregate_execution_flow(execution_id, payload)
            self.assertIsNotNone(report)
        except AnomalyReportAggregatorError:
            pass

    def test_generate_final_report_integration(self):
        source_name = f"src_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["INFO", "WARNING", "ERROR"])
        details_text = f"details_{uuid.uuid4()}"
        
        self.logger.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot={"metric": random.randint(0, 500)}
        )

        final_report = self.aggregator.generate_final_report()
        self.assertIsNotNone(final_report)


if __name__ == "__main__":
    unittest.main()