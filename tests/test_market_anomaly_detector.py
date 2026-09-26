import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_anomaly_detector import MarketAnomalyDetector


class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.mock_db_storage = MagicMock()
        self.mock_market_parser = MagicMock()
        self.mock_alert_dispatcher = MagicMock()
        self.mock_insider_tracker = MagicMock()

        self.detector = MarketAnomalyDetector(
            db_storage=self.mock_db_storage,
            market_parser=self.mock_market_parser,
            market_portfolio_alert_dispatcher=self.mock_alert_dispatcher,
            market_insider_activity_tracker=self.mock_insider_tracker
        )

    def test_detect_anomalies_success(self):
        random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_price = round(random.uniform(10.0, 1500.0), 2)
        random_volume = random.randint(10000, 5000000)
        random_html_id = uuid.uuid4().hex

        raw_html = f"<html><body><div id='{random_html_id}'>Price: {random_price}, Volume: {random_volume}</div></body></html>"

        self.mock_market_parser.fetch_market_data.return_value = raw_html

        anomalies = self.detector.analyze_and_detect(random_ticker)

        self.assertIsInstance(anomalies, list)
        self.mock_market_parser.fetch_market_data.assert_called_once_with(random_ticker)
        self.mock_db_storage.save_anomaly_audit.assert_called()

    def test_market_parser_integration_failure_propagates(self):
        random_ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        random_error_msg = f"Network timeout {uuid.uuid4().hex}"

        with patch('skills.market_anomaly_detector.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(random_error_msg)

            with self.assertRaises(requests.exceptions.RequestException):
                self.detector.analyze_and_detect(random_ticker)

            self.mock_db_storage.save_anomaly_audit.assert_not_called()

    def test_anomaly_payload_structure_and_random_generation(self):
        random_ticker = ''.join(random.choices(string.ascii_uppercase, k=6))
        random_token = uuid.uuid4().hex
        random_soup_text = f"ANOMALY_DETECTED_{random_token}"

        mock_stream = io.BytesIO(random_soup_text.encode('utf-8'))

        with patch('skills.market_anomaly_detector.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_response.text = random_soup_text
            mock_get.return_value = mock_response

            result = self.detector.inspect_stream_anomaly(random_ticker)

            self.assertIn("anomaly_score", result)
            self.assertIn("ticker", result)
            self.assertEqual(result["ticker"], random_ticker)
            self.assertIsInstance(result["anomaly_score"], float)

    def test_alert_dispatcher_invoked_on_critical_anomaly(self):
        random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_event_id = uuid.uuid4().hex
        random_threshold = random.randint(90, 99)

        with patch.object(self.detector, '_calculate_anomaly_index', return_value=float(random_threshold + 5)):
            self.detector.evaluate_critical_thresholds(random_ticker, random_threshold, random_event_id)

            self.mock_alert_dispatcher.dispatch_alert.assert_called_once()
            args, kwargs = self.mock_alert_dispatcher.dispatch_alert.call_args

            dispatched_payload = args[0] if args else kwargs.get('payload')
            self.assertEqual(dispatched_payload['ticker'], random_ticker)
            self.assertEqual(dispatched_payload['event_id'], random_event_id)

    def test_insider_tracker_integration_returns_strict_data(self):
        random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_insider_name = f"Person_{uuid.uuid4().hex[:8]}"
        random_shares_traded = random.randint(500, 100000)

        self.mock_insider_tracker.get_recent_trades.return_value = {
            "insider": random_insider_name,
            "shares": random_shares_traded,
            "flag": "ACCUMULATION"
        }

        analysis = self.detector.correlate_with_insider_activity(random_ticker)

        self.assertEqual(analysis["insider"], random_insider_name)
        self.assertEqual(analysis["shares"], random_shares_traded)
        self.mock_insider_tracker.get_recent_trades.assert_called_once_with(random_ticker)


if __name__ == '__main__':
    unittest.main()