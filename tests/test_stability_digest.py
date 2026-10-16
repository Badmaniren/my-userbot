import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.stability_digest import StabilityDigest, StabilityDigestError
from skills.anomaly_correlator import AnomalyCorrelator
from skills.anomaly_logger import AnomalyLogger


class TestStabilityDigest(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.9)

        self.mock_detector = MagicMock()
        self.mock_telemetry = MagicMock()

        self.digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.mock_detector,
            system_telemetry=self.mock_telemetry
        )

    def test_init_sets_attributes(self):
        rnd_repo = f"/var/git/{uuid.uuid4().hex}"
        det = MagicMock()
        tel = MagicMock()

        sd = StabilityDigest(rnd_repo, det, tel)

        self.assertEqual(sd.repo_path, rnd_repo)
        self.assertEqual(sd.anomaly_detector, det)
        self.assertEqual(sd.system_telemetry, tel)

    def test_generate_digest_success(self):
        rnd_summary_key = uuid.uuid4().hex
        rnd_summary_val = random.randint(100, 999)
        rnd_anomaly_name = uuid.uuid4().hex

        self.mock_telemetry.get_telemetry_summary.return_value = {rnd_summary_key: rnd_summary_val}
        self.mock_detector.detect_anomalies.return_value = [{"anomaly": rnd_anomaly_name}]

        exec_id = uuid.uuid4().hex
        result = self.digest.generate_digest(execution_id=exec_id)

        self.assertIn("summary", result)
        self.assertIn("anomalies", result)
        self.assertEqual(result["summary"][rnd_summary_key], rnd_summary_val)
        self.assertEqual(result["anomalies"][0]["anomaly"], rnd_anomaly_name)
        self.mock_telemetry.get_telemetry_summary.assert_called_once()
        self.mock_detector.detect_anomalies.assert_called_once()

    def test_generate_digest_handles_telemetry_exception(self):
        err_msg = uuid.uuid4().hex
        self.mock_telemetry.get_telemetry_summary.side_effect = Exception(err_msg)

        with self.assertRaises(StabilityDigestError) as ctx:
            self.digest.generate_digest()

        self.assertIn(err_msg, str(ctx.exception))

    def test_generate_digest_handles_detector_exception(self):
        err_msg = uuid.uuid4().hex
        self.mock_detector.detect_anomalies.side_effect = Exception(err_msg)
        
        with self.assertRaises(StabilityDigestError) as ctx:
            self.digest.generate_digest()

        self.assertIn(err_msg, str(ctx.exception))

    def test_export_digest_stream(self):
        stream_id = uuid.uuid4().hex
        expected_snapshot = {
            uuid.uuid4().hex: random.randint(1, 100),
            "stream_id": stream_id
        }
        self.mock_telemetry.collect_snapshot.return_value = expected_snapshot

        result = self.digest.export_digest_stream(stream_id)

        self.assertEqual(result, expected_snapshot)
        self.mock_telemetry.collect_snapshot.assert_called_once_with(stream_id)

    def test_analyze_digest_trends_stable(self):
        metric = uuid.uuid4().hex
        val = random.randint(50, 100)
        history = [val, val]
        self.mock_telemetry.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric)

        self.assertEqual(result["metric"], metric)
        self.assertEqual(result["history"], history)
        self.assertEqual(result["trend"], "stable")

    def test_analyze_digest_trends_increasing(self):
        metric = uuid.uuid4().hex
        low = random.randint(1, 40)
        high = random.randint(60, 100)
        history = [low, high]
        self.mock_telemetry.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric)
        
        self.assertEqual(result["metric"], metric)
        self.assertEqual(result["trend"], "increasing")

    def test_analyze_digest_trends_decreasing(self):
        metric = uuid.uuid4().hex
        low = random.randint(1, 40)
        high = random.randint(60, 100)
        history = [high, low]
        self.mock_telemetry.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric)

        self.assertEqual(result["metric"], metric)
        self.assertEqual(result["trend"], "decreasing")

    def test_analyze_digest_trends_exception(self):
        metric = uuid.uuid4().hex
        err_msg = uuid.uuid4().hex
        self.mock_telemetry.get_metric_history.side_effect = Exception(err_msg)

        with self.assertRaises(StabilityDigestError) as ctx:
            self.digest.analyze_digest_trends(metric)

        self.assertIn(err_msg, str(ctx.exception))

    def test_composition_with_real_submodules(self):
        real_logger = AnomalyLogger(self.log_path)
        real_correlator = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            detector=self.mock_detector,
            logger=real_logger
        )

        metric_name = uuid.uuid4().hex
        val = random.randint(10, 500)

        with patch.object(self.mock_telemetry, 'get_metric_history', return_value=[val - 10, val]):
            res = self.digest.analyze_digest_trends(metric_name)
            self.assertEqual(res["trend"], "increasing")
            self.assertEqual(res["metric"], metric_name)