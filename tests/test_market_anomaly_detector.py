import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_anomaly_detector import MarketAnomalyDetector

class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.random_db_url = f"sqlite:///{uuid.uuid4().hex}.db"
        self.mock_db_storage = MagicMock()
        self.detector = MarketAnomalyDetector(db_storage=self.mock_db_storage)

    def test_detect_anomalies_success(self):
        target_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_price = round(random.uniform(10.0, 1500.0), 2)
        random_volume = random.randint(1000, 1000000)

        raw_payload = f'{{"symbol": "{target_symbol}", "price": {random_price}, "volume": {random_volume}}}'.encode('utf-8')
        mock_stream = io.BytesIO(raw_payload)

        with patch('skills.market_anomaly_detector.market_parser') as mock_parser:
            mock_parser.parse_stream.return_value = {
                "symbol": target_symbol,
                "price": random_price,
                "volume": random_volume
            }

            result = self.detector.analyze_market_feed(mock_stream)

            self.assertTrue(result)
            self.mock_db_storage.save_anomaly.assert_called_once()
            saved_data = self.mock_db_storage.save_anomaly.call_args[0][0]
            self.assertEqual(saved_data["symbol"], target_symbol)

    def test_detect_anomalies_handles_parser_exception_correctly(self):
        corrupted_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(corrupted_bytes)
        expected_error_msg = f"Parsing failed for uuid: {uuid.uuid4().hex}"

        with patch('skills.market_anomaly_detector.market_parser') as mock_parser:
            mock_parser.parse_stream.side_effect = ValueError(expected_error_msg)

            with self.assertRaises(ValueError) as ctx:
                self.detector.analyze_market_feed(mock_stream)

            self.assertIn(expected_error_msg, str(ctx.exception))
            self.mock_db_storage.save_anomaly.assert_not_called()

    def test_anomaly_threshold_trigger(self):
        anomaly_id = uuid.uuid4().hex
        high_volatility_score = round(random.uniform(85.0, 99.9), 2)

        with patch('skills.market_anomaly_detector.market_insider_activity_tracker') as mock_tracker:
            mock_tracker.get_activity_index.return_value = {
                "id": anomaly_id,
                "score": high_volatility_score,
                "flagged": True
            }

            alert_dispatch_target = f"channel_{uuid.uuid4().hex[:8]}"
            with patch('skills.market_portfolio_alert_dispatcher.dispatch') as mock_dispatcher:
                self.detector.evaluate_insider_metrics(anomaly_id)

                mock_tracker.get_activity_index.assert_called_once_with(anomaly_id)
                self.mock_db_storage.log_audit_event.assert_called()

                audit_call_args = self.mock_db_storage.log_audit_event.call_args[0][0]
                self.assertEqual(audit_call_args["anomaly_id"], anomaly_id)
                self.assertEqual(audit_call_args["score"], high_volatility_score)

    def test_robust_database_error_handling(self):
        random_payload_id = uuid.uuid4().hex
        self.mock_db_storage.save_anomaly.side_effect = ConnectionError(f"DB down: {uuid.uuid4().hex}")

        mock_stream = io.BytesIO(b'{"test": "data"}')

        with patch('skills.market_anomaly_detector.market_parser') as mock_parser:
            mock_parser.parse_stream.return_value = {"id": random_payload_id}

            with self.assertRaises(ConnectionError):
                self.detector.analyze_market_feed(mock_stream)

if __name__ == '__main__':
    unittest.main()