import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector_main

class TestMarketAnomalyDetector(unittest.TestCase):
    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string.ascii_letters, k=8))
        self.ticker = self.rand_str().upper()
        self.anomaly_id = str(uuid.uuid4())
        self.volume = random.randint(1000, 10000000)
        self.price = random.uniform(10.0, 5000.0)
        self.run_id = str(uuid.uuid4())
        self.chat_id = random.randint(10000, 999999)
        self.strategy_id = str(uuid.uuid4())
        self.stream_name = self.rand_str()
        self.insider_id = str(uuid.uuid4())

    def test_analyze_market_stream_success(self):
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            "ticker": self.ticker,
            "volume": self.volume,
            "anomaly_id": self.anomaly_id
        }
        mock_db = MagicMock()
        mock_dispatcher = MagicMock()

        detector = MarketAnomalyDetector(
            db_storage=mock_db,
            market_parser=mock_parser,
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        result = detector.analyze_market_stream(self.ticker)
        self.assertEqual(result["ticker"], self.ticker)
        self.assertEqual(result["volume"], self.volume)
        self.assertEqual(result["anomaly_id"], self.anomaly_id)
        mock_db.save.assert_called_once_with(result)
        mock_dispatcher.dispatch.assert_called_once_with(result)

    def test_process_data_stream(self):
        mock_collector = MagicMock()
        detector = MarketAnomalyDetector(market_portfolio_collector_agent=mock_collector)
        res = detector.process_data_stream(self.stream_name)
        mock_collector.fetch_stream.assert_called_once_with(self.stream_name)
        self.assertTrue(res)

    def test_correlate_insider_activity_high(self):
        mock_tracker = MagicMock()
        score_val = random.uniform(5.1, 15.0)
        mock_tracker.get_activity_score.return_value = {"score": score_val}
        detector = MarketAnomalyDetector(market_insider_activity_tracker=mock_tracker)
        payload = {"insider_id": self.insider_id}
        res = detector.correlate_insider_activity(payload)
        mock_tracker.get_activity_score.assert_called_once_with(self.insider_id)
        self.assertTrue(res)

    def test_correlate_insider_activity_low(self):
        mock_tracker = MagicMock()
        score_val = random.uniform(0.0, 5.0)
        mock_tracker.get_activity_score.return_value = {"score": score_val}
        detector = MarketAnomalyDetector(market_insider_activity_tracker=mock_tracker)
        payload = {"insider_id": self.insider_id}
        res = detector.correlate_insider_activity(payload)
        mock_tracker.get_activity_score.assert_called_once_with(self.insider_id)
        self.assertFalse(res)

    def test_notify_subscribers(self):
        mock_notifier = MagicMock()
        msg = self.rand_str()
        detector = MarketAnomalyDetector(market_portfolio_telegram_notifier=mock_notifier)
        detector.notify_subscribers(self.chat_id, msg)
        mock_notifier.send_alert.assert_called_once_with(chat_id=self.chat_id, message=msg)

    def test_evaluate_backtest_with_mock(self):
        mock_backtester = MagicMock()
        expected_ret = {"strategy_id": self.strategy_id, "success": random.choice([True, False])}
        mock_backtester.run_simulation.return_value = expected_ret
        detector = MarketAnomalyDetector(market_portfolio_backtester=mock_backtester)
        res = detector.evaluate_backtest(self.strategy_id)
        mock_backtester.run_simulation.assert_called_once_with(self.strategy_id)
        self.assertEqual(res, expected_ret)

    def test_evaluate_backtest_fallback(self):
        detector = MarketAnomalyDetector()
        res = detector.evaluate_backtest(self.strategy_id)
        self.assertEqual(res["strategy_id"], self.strategy_id)
        self.assertTrue(res["success"])

    def test_market_anomaly_detector_main_triggered_price_volume(self):
        payload = {
            "run_id": self.run_id,
            "market_data": {"price": 1500.0, "volume": 6000000},
            "insider_metrics": {"activity_index": 0.1},
            "threshold": 0.5
        }
        res = market_anomaly_detector_main(payload)
        self.assertEqual(res["run_id"], self.run_id)
        self.assertTrue(res["anomaly_detected"])
        self.assertEqual(res["price"], 1500.0)
        self.assertEqual(res["volume"], 6000000)

    def test_market_anomaly_detector_main_triggered_activity(self):
        threshold = random.uniform(0.1, 0.4)
        activity_index = threshold + random.uniform(0.1, 0.5)
        payload = {
            "run_id": self.run_id,
            "market_data": {"price": 100.0, "volume": 100},
            "insider_metrics": {"activity_index": activity_index},
            "threshold": threshold
        }
        res = market_anomaly_detector_main(payload)
        self.assertEqual(res["run_id"], self.run_id)
        self.assertTrue(res["anomaly_detected"])
        self.assertEqual(res["activity_index"], activity_index)

    def test_market_anomaly_detector_main_not_triggered(self):
        threshold = random.uniform(0.6, 0.9)
        payload = {
            "run_id": self.run_id,
            "market_data": {"price": 100.0, "volume": 100},
            "insider_metrics": {"activity_index": 0.1},
            "threshold": threshold
        }
        res = market_anomaly_detector_main(payload)
        self.assertEqual(res["run_id"], self.run_id)
        self.assertFalse(res["anomaly_detected"])

if __name__ == '__main__':
    unittest.main()