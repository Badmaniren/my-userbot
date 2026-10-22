import unittest
import tempfile
import os
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.log")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_workflow_real_data(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(10.0, 500.0), 2)

        details = {
            "error_code": random.randint(500, 599),
            "description": f"Random failure description {uuid.uuid4()}"
        }
        telemetry = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.assertIsNotNone(log_result)
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл должен быть физически создан в файловой системе")

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result)

        final_report = self.hub.generate_final_report()
        self.assertIsInstance(final_report, (dict, list, str))

    def test_integration_exception_propagation(self):
        invalid_metric_name = ""
        invalid_value = "not_a_float"

        with self.assertRaises(Exception) as context:
            self.hub.aggregate_and_report(
                metric_name=invalid_metric_name,
                value=invalid_value
            )

        self.assertTrue(
            isinstance(context.exception, (AnomalyReportAggregatorError, TypeError, ValueError)),
            f"Исключение должно корректно пробрасываться, получено: {type(context.exception)}"
        )


if __name__ == '__main__':
    unittest.main()