import unittest
import uuid
import random
import tempfile
import shutil
import os

from skills.stability_digest import StabilityDigest, StabilityDigestError
from skills.anomaly_correlator import AnomalyCorrelator
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_detector import AnomalyDetectorError
from skills.system_telemetry import SystemTelemetryError

class RealTelemetryMock:
    def __init__(self, data=None):
        self.data = data or {}
        self.history = [random.randint(10, 50), random.randint(50, 100)]

    def get_telemetry_summary(self):
        return {"status": "nominal", "rand_metric": random.randint(1, 100), **self.data}

    def collect_snapshot(self, stream_id: str):
        return {"stream_id": stream_id, "snapshot_data": random.random()}

    def get_metric_history(self, metric_name: str):
        return self.history

class RealDetectorMock:
    def detect_anomalies(self):
        return [{"anomaly_id": str(uuid.uuid4()), "severity": "LOW"}]

class IntegrationTestStabilityDigest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"test_log_{uuid.uuid4()}.json")
        self.repo_path = self.test_dir

        self.telemetry = RealTelemetryMock()
        self.detector = RealDetectorMock()

        self.digest_module = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.detector,
            system_telemetry=self.telemetry
        )

        self.logger = AnomalyLogger(log_path=self.log_path)
        self.correlator = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.uniform(0.1, 0.9),
            detector=self.detector,
            logger=self.logger
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_generate_digest_and_logger(self):
        rand_source = f"source_{uuid.uuid4()}"
        rand_severity = random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        rand_details = {"info": uuid.uuid4().hex}

        digest_res = self.digest_module.generate_digest(execution_id=str(uuid.uuid4()))

        self.assertIn("summary", digest_res)
        self.assertIn("anomalies", digest_res)

        snapshot = self.digest_module.export_digest_stream(stream_id=str(uuid.uuid4()))
        self.assertIn("stream_id", snapshot)

        self.logger.log_anomaly(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=digest_res["summary"]
        )

        anomalies_list = self.logger.get_anomalies()
        self.assertTrue(any(a["source"] == rand_source for a in anomalies_list))

    def test_integration_analyze_trends_with_correlator(self):
        metric_name = f"cpu_usage_{uuid.uuid4().hex[:6]}"
        trend_result = self.digest_module.analyze_digest_trends(metric_name)

        self.assertEqual(trend_result["metric"], metric_name)
        self.assertIn(trend_result["trend"], ["stable", "increasing", "decreasing"])

        correlation = self.correlator.correlate_metric(metric_name, random.randint(100, 500))
        self.assertIsInstance(correlation, (bool, dict, list, type(None)))

if __name__ == "__main__":
    unittest.main()