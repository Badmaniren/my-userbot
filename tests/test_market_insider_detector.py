import unittest
from unittest.mock import MagicMock, patch
import uuid
import random

from skills.market_insider_detector import MarketInsiderDetector


class TestMarketInsiderDetector(unittest.TestCase):

    def setUp(self):
        self.symbol = f"TICK_{uuid.uuid4().hex[:6]}"
        self.run_token = uuid.uuid4().hex
        self.mock_db = MagicMock()
        self.mock_parser = MagicMock()
        self.detector = MarketInsiderDetector(db_storage=self.mock_db, market_parser=self.mock_parser)

    def test_detect_insider_activity_no_parser(self):
        detector_no_parser = MarketInsiderDetector(db_storage=self.mock_db, market_parser=None)
        res = detector_no_parser.detect_insider_activity(self.symbol, 2.0, 5.0, 10)
        self.assertEqual(res, [])

    def test_detect_insider_activity_insufficient_data(self):
        self.mock_parser.get_historical_data.return_value = [{"volume": random.randint(100, 500), "close": 10.0}]
        res = self.detector.detect_insider_activity(self.symbol, 2.0, 5.0, 5)
        self.assertEqual(res, [])

    def test_detect_insider_activity_success(self):
        lookback = 5
        base_vol = 1000
        multiplier = 3.0
        pct_change = 10.0

        data = []
        for i in range(lookback - 1):
            data.append({"volume": base_vol, "close": 100.0 + i})

        spike_vol = int(base_vol * multiplier)
        spike_price = 100.0 + lookback
        future_price = spike_price * (1.0 + (pct_change / 100.0) + 0.01)

        data.append({"volume": spike_vol, "close": spike_price})
        data.append({"volume": base_vol, "close": future_price})

        self.mock_parser.get_historical_data.return_value = data

        alerts = self.detector.detect_insider_activity(self.symbol, multiplier, pct_change, lookback)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0]["symbol"], self.symbol)
        self.assertEqual(alerts[0]["volume"], spike_vol)
        self.mock_db.save_alert.assert_called()

    def test_analyze_activity_anomaly_detected(self):
        vol = random.randint(600000, 1000000)
        shift = random.uniform(2.5, 5.0)
        payload = {"volume": vol, "price_shift": shift}

        result = self.detector.analyze_activity(self.symbol, payload, self.run_token)

        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["run_token"], self.run_token)
        self.assertEqual(result["ticker"], self.symbol)
        self.mock_db.save_insider_event.assert_called_once()

    def test_analyze_activity_no_anomaly(self):
        vol = random.randint(1000, 100000)
        shift = random.uniform(0.1, 1.5)
        payload = {"volume": vol, "price_shift": shift}

        result = self.detector.analyze_activity(self.symbol, payload, self.run_token)

        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["run_token"], self.run_token)
        self.assertEqual(result["ticker"], self.symbol)
        self.mock_db.save_insider_event.assert_not_called()
        self.mock_db.save_alert.assert_not_called()


if __name__ == "__main__":
    unittest.main()