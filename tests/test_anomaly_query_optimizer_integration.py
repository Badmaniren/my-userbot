import unittest
import os
import tempfile
import uuid
import random

from skills.anomaly_query_optimizer import AnomalyQueryOptimizer, QueryFilter, optimize_query, filter_logs_by_index
from skills.anomaly_logger import AnomalyLogger
from skills.extractor_tool_1792595633 import ExtractorTool


class TestAnomalyQueryOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"test_anomalies_{uuid.uuid4().hex}.log")
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.extractor = ExtractorTool()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_query_optimization_and_logging(self):
        unique_tag = f"err_{uuid.uuid4().hex[:8]}"
        random_timestamp = random.randint(1600000000, 1900000000)
        severity_level = random.choice(["HIGH", "CRITICAL", "MEDIUM"])

        details_data = f"<anomaly tag='{unique_tag}' severity='{severity_level}'>System failure at {random_timestamp}</anomaly>"
        extracted_meta = self.extractor.extract(details_data)

        self.logger.log_anomaly(
            source=f"service_{uuid.uuid4().hex[:6]}",
            severity=severity_level,
            details=details_data,
            telemetry_snapshot={"cpu_load": random.random()}
        )

        optimizer = AnomalyQueryOptimizer(optimizer_id=uuid.uuid4().hex, storage_path=self.log_path)

        index_status = optimizer.build_index([unique_tag])
        self.assertTrue(index_status)

        base_query = "SELECT * FROM anomalies"
        q_filter = QueryFilter(start_time=random_timestamp, tag=unique_tag)
        optimized_q = optimizer.optimize_query(base_query, q_filter)

        self.assertIn(f"timestamp >= {random_timestamp}", optimized_q)
        self.assertIn(f"tag == '{unique_tag}'", optimized_q)

        hinted_query = optimize_query(optimized_q, index_hint=unique_tag)
        self.assertIn(f"index_hint = '{unique_tag}'", hinted_query)

        executed_results = optimizer.execute(hinted_query)
        self.assertGreater(len(executed_results), 0)

        filtered_logs = filter_logs_by_index(executed_results, unique_tag)
        self.assertGreater(len(filtered_logs), 0)
        self.assertIn(unique_tag, str(filtered_logs[0]))

        parsed_filters = optimizer.parse_filters(f"SELECT * FROM logs WHERE severity '{severity_level}' AND timestamp {random_timestamp}")
        self.assertEqual(parsed_filters.get('severity'), severity_level)
        self.assertEqual(parsed_filters.get('timestamp'), str(random_timestamp))

        optimizer.clear_cache()
        self.assertEqual(len(optimizer._query_cache), 0)


if __name__ == "__main__":
    unittest.main()