import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
from skills.stability_digest import StabilityDigest, StabilityDigestError


class TestStabilityDigest(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.anomaly_detector_mock = MagicMock()
        self.system_telemetry_mock = MagicMock()
        self.digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector_mock,
            system_telemetry=self.system_telemetry_mock
        )

    def test_generate_digest_with_detect_anomalies(self):
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_anomalies = [uuid.uuid4().hex, uuid.uuid4().hex]
        
        self.system_telemetry_mock.get_telemetry_summary.return_value = expected_summary
        del self.anomaly_detector_mock.analyze_anomalies
        self.anomaly_detector_mock.detect_anomalies.return_value = expected_anomalies

        exec_id = uuid.uuid4().hex
        result = self.digest.generate_digest(execution_id=exec_id)

        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["anomalies"], expected_anomalies)
        self.system_telemetry_mock.get_telemetry_summary.assert_called_once()
        self.anomaly_detector_mock.detect_anomalies.assert_called_once()

    def test_generate_digest_with_analyze_anomalies(self):
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_anomalies = {uuid.uuid4().hex: random.random()}
        
        self.system_telemetry_mock.get_telemetry_summary.return_value = expected_summary
        del self.anomaly_detector_mock.detect_anomalies
        self.anomaly_detector_mock.analyze_anomalies.return_value = expected_anomalies

        result = self.digest.generate_digest()

        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["anomalies"], expected_anomalies)
        self.system_telemetry_mock.get_telemetry_summary.assert_called_once()
        self.anomaly_detector_mock.analyze_anomalies.assert_called_once()

    def test_generate_digest_no_anomaly_methods(self):
        expected_summary = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.system_telemetry_mock.get_telemetry_summary.return_value = expected_summary
        
        del self.anomaly_detector_mock.detect_anomalies
        del self.anomaly_detector_mock.analyze_anomalies

        result = self.digest.generate_digest()

        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["anomalies"], [])

    def test_generate_digest_raises_stability_digest_error(self):
        err_msg = uuid.uuid4().hex
        self.system_telemetry_mock.get_telemetry_summary.side_effect = Exception(err_msg)

        with self.assertRaises(StabilityDigestError) as ctx:
            self.digest.generate_digest()
        
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_digest_stream(self):
        stream_id = uuid.uuid4().hex
        expected_snapshot = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.system_telemetry_mock.collect_snapshot.return_value = expected_snapshot

        result = self.digest.export_digest_stream(stream_id)

        self.assertEqual(result, expected_snapshot)
        self.system_telemetry_mock.collect_snapshot.assert_called_once_with(stream_id)

    def test_analyze_digest_trends_stable(self):
        metric_name = uuid.uuid4().hex
        val = random.randint(10, 50)
        history = [val, val]
        self.system_telemetry_mock.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric_name)

        self.assertEqual(result["metric"], metric_name)
        self.assertEqual(result["history"], history)
        self.assertEqual(result["trend"], "stable")
        self.system_telemetry_mock.get_metric_history.assert_called_once_with(metric_name)

    def test_analyze_digest_trends_increasing(self):
        metric_name = uuid.uuid4().hex
        base_val = random.randint(1, 50)
        history = [base_val, base_val + random.randint(1, 50)]
        self.system_telemetry_mock.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric_name)

        self.assertEqual(result["trend"], "increasing")

    def test_analyze_digest_trends_decreasing(self):
        metric_name = uuid.uuid4().hex
        base_val = random.randint(51, 100)
        history = [base_val, base_val - random.randint(1, 50)]
        self.system_telemetry_mock.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric_name)

        self.assertEqual(result["trend"], "decreasing")

    def test_analyze_digest_trends_empty_history(self):
        metric_name = uuid.uuid4().hex
        history = []
        self.system_telemetry_mock.get_metric_history.return_value = history

        result = self.digest.analyze_digest_trends(metric_name)

        self.assertEqual(result["trend"], "stable")

    def test_analyze_digest_trends_raises_stability_digest_error(self):
        metric_name = uuid.uuid4().hex
        err_msg = uuid.uuid4().hex
        self.system_telemetry_mock.get_metric_history.side_effect = Exception(err_msg)

        with self.assertRaises(StabilityDigestError) as ctx:
            self.digest.analyze_digest_trends(metric_name)
        
        self.assertIn(err_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()