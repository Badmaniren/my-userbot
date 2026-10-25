import unittest
import uuid
import random
import tempfile
import os

from skills.stability_digest import StabilityDigest, StabilityDigestError
from skills.system_telemetry import SystemTelemetry
from skills.anomaly_correlator import AnomalyCorrelator


class TestStabilityDigestIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        
        self.system_telemetry = SystemTelemetry(self.repo_path)
        self.anomaly_correlator = AnomalyCorrelator(self.repo_path)
        
        self.stability_digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_correlator,
            system_telemetry=self.system_telemetry
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_digest_and_trends_integration(self):
        random_metric = f"metric_{uuid.uuid4().hex[:8]}"
        random_values = [random.randint(1, 100), random.randint(101, 200)]
        
        self.system_telemetry.metrics[random_metric] = random_values
        
        digest_result = self.stability_digest.generate_digest(execution_id=uuid.uuid4().hex)
        
        self.assertIn("summary", digest_result)
        self.assertIn("anomalies", digest_result)
        
        trend_result = self.stability_digest.analyze_digest_trends(random_metric)
        
        self.assertEqual(trend_result["metric"], random_metric)
        self.assertEqual(trend_result["history"], random_values)
        self.assertEqual(trend_result["trend"], "increasing")

    def test_export_digest_stream_integration(self):
        random_stream_id = uuid.uuid4().hex
        
        snapshot = self.stability_digest.export_digest_stream(random_stream_id)
        
        self.assertIsInstance(snapshot, dict)

    def test_stability_digest_error_handling(self):
        with self.assertRaises(StabilityDigestError):
            self.stability_digest.analyze_digest_trends(f"non_existent_metric_{uuid.uuid4().hex}")


if __name__ == "__main__":
    unittest.main()