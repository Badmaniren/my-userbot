import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.stability_digest import StabilityDigest, StabilityDigestError
from skills.anomaly_detector import AnomalyDetector
from skills.system_telemetry import SystemTelemetry


class TestStabilityDigest(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.anomaly_detector = MagicMock(spec=AnomalyDetector)
        self.system_telemetry = MagicMock(spec=SystemTelemetry)
        self.digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )

    def test_init_sets_attributes(self):
        rnd_path = f"/var/repo/{uuid.uuid4().hex}"
        det = MagicMock(spec=AnomalyDetector)
        tel = MagicMock(spec=SystemTelemetry)
        digest = StabilityDigest(repo_path=rnd_path, anomaly_detector=det, system_telemetry=tel)
        self.assertEqual(digest.repo_path, rnd_path)
        self.assertEqual(digest.anomaly_detector, det)
        self.assertEqual(digest.system_telemetry, tel)

    def test_generate_digest_success(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.uniform(10.0, 100.0)
        execution_id = uuid.uuid4().hex

        self.system_telemetry.get_telemetry_summary.return_value = {
            metric_name: [metric_value],
            "execution_id": execution_id
        }
        self.anomaly_detector.detect_anomalies.return_value = {
            metric_name: False
        }

        result = self.digest.generate_digest()

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("anomalies", result)
        self.assertEqual(result["summary"][metric_name], [metric_value])
        self.assertEqual(result["anomalies"][metric_name], False)

    def test_generate_digest_handles_exception(self):
        rnd_msg = uuid.uuid4().hex
        self.system_telemetry.get_telemetry_summary.side_effect = Exception(rnd_msg)

        with self.assertRaises(StabilityDigestError) as ctx:
            self.digest.generate_digest()
        
        self.assertIn(rnd_msg, str(ctx.exception))

    def test_export_digest_stream(self):
        stream_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        snapshot_data = {metric_name: random.randint(100, 999)}

        self.system_telemetry.collect_snapshot.return_value = snapshot_data

        result = self.digest.export_digest_stream(stream_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result[metric_name], snapshot_data[metric_name])
        self.system_telemetry.collect_snapshot.assert_called_once_with(stream_id)

    def test_analyze_digest_trends_with_valid_data(self):
        metric_name = uuid.uuid4().hex
        history = [random.uniform(0, 50) for _ in range(5)]
        
        self.system_telemetry.get_metric_history.return_value = history

        analysis = self.digest.analyze_digest_trends(metric_name)

        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get("metric"), metric_name)
        self.assertEqual(analysis.get("history"), history)
        self.assertIn("trend", analysis)

    def test_analyze_digest_trends_error(self):
        metric_name = uuid.uuid4().hex
        rnd_err = uuid.uuid4().hex
        self.system_telemetry.get_metric_history.side_effect = RuntimeError(rnd_err)

        with self.assertRaises(StabilityDigestError):
            self.digest.analyze_digest_trends(metric_name)


if __name__ == '__main__':
    unittest.main()