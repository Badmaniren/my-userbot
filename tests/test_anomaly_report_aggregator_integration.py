import os
import random
import tempfile
import unittest
import uuid
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import (
    AnomalyReportAggregator,
    AnomalyReportAggregatorError,
)


class TestAnomalyReportAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(
            self.temp_dir.name, f"test_anomaly_{uuid.uuid4().hex}.log"
        )
        self.logger = AnomalyLogger(log_path=self.log_file)
        self.aggregator = AnomalyReportAggregator(
            log_path=self.log_file,
            logger=self.logger,
            threshold=random.uniform(50.0, 80.0)
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_aggregate_and_report_real_pipeline(self):
        random_metric = f"metric_{uuid.uuid4().hex[:8]}"
        random_value = round(random.uniform(10.0, 100.0), 3)

        report = self.aggregator.aggregate_and_report(random_metric, random_value)
        self.assertIsInstance(report, (dict, list))

        final_report = self.aggregator.generate_final_report()
        self.assertIsInstance(final_report, (dict, list))

        logged_anomalies = self.logger.get_anomalies()
        self.assertIsInstance(logged_anomalies, list)

    def test_aggregate_execution_flow_with_payload_conversion(self):
        execution_id = f"exec_{uuid.uuid4().hex}"
        random_num = round(random.uniform(100.5, 999.9), 2)
        payload = {
            f"key_str_float_{uuid.uuid4().hex[:6]}": str(random_num),
            f"key_raw_str_{uuid.uuid4().hex[:6]}": f"val_{uuid.uuid4().hex[:4]}",
            f"key_numeric_{uuid.uuid4().hex[:6]}": random.randint(1, 50),
        }

        report = self.aggregator.aggregate_execution_flow(execution_id, payload)
        self.assertIsInstance(report, (dict, list))

        persisted_logs = self.logger.get_structured_report()
        self.assertIsInstance(persisted_logs, (dict, list))
        self.assertTrue(os.path.exists(self.log_file))

    def test_generate_final_report_matches_logger_state(self):
        random_source = f"src_{uuid.uuid4().hex[:6]}"
        random_details = f"details_{uuid.uuid4().hex}"
        random_snapshot = {"rand_key": random.randint(100, 999)}

        self.logger.log_anomaly(
            source=random_source,
            severity="HIGH",
            details=random_details,
            telemetry_snapshot=random_snapshot,
        )

        final_report = self.aggregator.generate_final_report()
        self.assertIsInstance(final_report, (dict, list))

        report_str = str(final_report)
        self.assertIn(random_source, report_str)
        self.assertIn(random_details, report_str)

    def test_error_handling_wraps_in_anomaly_report_aggregator_error(self):
        class FaultyCorrelator:
            def correlate_metric(self, metric, value):
                raise ValueError("Inner correlation failed")

        faulty_aggregator = AnomalyReportAggregator(
            correlator=FaultyCorrelator(),
            logger=self.logger
        )

        with self.assertRaises(AnomalyReportAggregatorError):
            faulty_aggregator.aggregate_and_report("bad_metric", 123)


if __name__ == "__main__":
    unittest.main()