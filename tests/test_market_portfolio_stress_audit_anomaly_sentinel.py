import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_audit_anomaly_sentinel import start_new


class TestMarketPortfolioStressAuditAnomalySentinel(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.random_threshold = round(random.uniform(0.01, 0.99), 4)
        self.random_metric = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_error_message = ''.join(random.choices(string.ascii_letters + string.whitespace, k=25))

    def test_start_new_success_anomaly_detected(self):
        mock_db = MagicMock()
        mock_anomaly_detector = MagicMock()
        mock_alert_dispatcher = MagicMock()

        expected_anomaly_score = round(random.uniform(1.0, 10.0), 2)
        mock_anomaly_detector.evaluate.return_value = {
            "is_anomaly": True,
            "score": expected_anomaly_score,
            "metric": self.random_metric
        }

        with patch('skills.market_portfolio_stress_audit_anomaly_sentinel.db_storage', mock_db), \
             patch('skills.market_portfolio_stress_audit_anomaly_sentinel.market_anomaly_detector', mock_anomaly_detector), \
             patch('skills.market_portfolio_stress_audit_anomaly_sentinel.market_portfolio_alert_dispatcher', mock_alert_dispatcher):

            result = start_new(
                portfolio_id=self.random_portfolio_id,
                audit_id=self.random_audit_id,
                threshold=self.random_threshold
            )

            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("anomaly_detected"))
            self.assertEqual(result.get("score"), expected_anomaly_score)
            mock_anomaly_detector.evaluate.assert_called_once()
            mock_alert_dispatcher.dispatch.assert_called_once()

    def test_start_new_no_anomaly(self):
        mock_db = MagicMock()
        mock_anomaly_detector = MagicMock()
        mock_alert_dispatcher = MagicMock()

        expected_anomaly_score = round(random.uniform(0.0, 0.49), 2)
        mock_anomaly_detector.evaluate.return_value = {
            "is_anomaly": False,
            "score": expected_anomaly_score,
            "metric": self.random_metric
        }

        with patch('skills.market_portfolio_stress_audit_anomaly_sentinel.db_storage', mock_db), \
             patch('skills.market_portfolio_stress_audit_anomaly_sentinel.market_anomaly_detector', mock_anomaly_detector), \
             patch('skills.market_portfolio_stress_audit_anomaly_sentinel.market_portfolio_alert_dispatcher', mock_alert_dispatcher):

            result = start_new(
                portfolio_id=self.random_portfolio_id,
                audit_id=self.random_audit_id,
                threshold=self.random_threshold
            )

            self.assertIsInstance(result, dict)
            self.assertFalse(result.get("anomaly_detected"))
            self.assertEqual(result.get("score"), expected_anomaly_score)
            mock_alert_dispatcher.dispatch.assert_not_called()

    def test_start_new_io_stream_handling(self):
        mock_db = MagicMock()
        mock_exporter = MagicMock()

        random_bytes = f"audit_payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_exporter.export_stream.return_value = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_stress_audit_anomaly_sentinel.db_storage', mock_db), \
             patch('skills.market_portfolio_stress_audit_anomaly_sentinel.market_portfolio_stress_audit_exporter_v2', mock_exporter):

            result = start_new(
                portfolio_id=self.random_portfolio_id,
                audit_id=self.random_audit_id,
                threshold=self.random_threshold
            )

            self.assertIsInstance(result, dict)
            mock_exporter.export_stream.assert_called_once()

    def test_start_new_exception_handling(self):
        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.evaluate.side_effect = RuntimeError(self.random_error_message)

        with patch('skills.market_portfolio_stress_audit_anomaly_sentinel.market_anomaly_detector', mock_anomaly_detector):
            with self.assertRaises(RuntimeError) as ctx:
                start_new(
                    portfolio_id=self.random_portfolio_id,
                    audit_id=self.random_audit_id,
                    threshold=self.random_threshold
                )
            self.assertIn(self.random_error_message, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()