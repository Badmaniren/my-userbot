import unittest
from unittest.mock import AsyncMock, MagicMock
import io
import json
import asyncio

from skills.market_activity_classifier import MarketActivityClassifier


class TestMarketActivityClassifier(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.classifier = MarketActivityClassifier(high_threshold=5.0, medium_threshold=2.0)

    def test_init_defaults(self):
        c = MarketActivityClassifier()
        self.assertEqual(c.high_threshold, 5.0)
        self.assertEqual(c.medium_threshold, 2.0)
        self.assertIsNone(c.db_storage)
        self.assertIsNone(c.alert_router)

    def test_init_custom_thresholds_and_deps(self):
        mock_db = MagicMock()
        mock_router = MagicMock()
        c = MarketActivityClassifier(high_threshold=10.0, medium_threshold=3.0, db_storage=mock_db, alert_router=mock_router)
        self.assertEqual(c.high_threshold, 10.0)
        self.assertEqual(c.medium_threshold, 3.0)
        self.assertEqual(c.db_storage, mock_db)
        self.assertEqual(c.alert_router, mock_router)

    def test_classify_low(self):
        # 100/100 = 1.0 (< 2.0)
        res = self.classifier.classify(100, 10, 100, 10)
        self.assertEqual(res, "Low")

    def test_classify_medium(self):
        # 250/100 = 2.5 (>= 2.0 and < 5.0)
        res = self.classifier.classify(250, 10, 100, 10)
        self.assertEqual(res, "Medium")

        # freq deviation medium
        res_freq = self.classifier.classify(100, 25, 100, 10)
        self.assertEqual(res_freq, "Medium")

    def test_classify_high(self):
        # 600/100 = 6.0 (>= 5.0)
        res = self.classifier.classify(600, 10, 100, 10)
        self.assertEqual(res, "High")

        # freq deviation high
        res_freq = self.classifier.classify(100, 60, 100, 10)
        self.assertEqual(res_freq, "High")

    def test_classify_edge_cases(self):
        self.assertEqual(self.classifier.classify(100, 10, 0, 10), "Low")
        self.assertEqual(self.classifier.classify(100, 10, -5, 10), "Low")
        self.assertEqual(self.classifier.classify(100, 10, None, 10), "Low")
        self.assertEqual(self.classifier.classify("invalid", 10, 100, 10), "Low")

    def test_parse_stream(self):
        data = {"symbol": "BTC", "volume": 500, "frequency": 30}
        json_bytes = json.dumps(data).encode('utf-8')

        stream = io.BytesIO(json_bytes)
        parsed = self.classifier.parse_stream(stream)
        self.assertEqual(parsed, data)

        parsed_dict = self.classifier.parse_stream(data)
        self.assertEqual(parsed_dict, data)

        parsed_str = self.classifier.parse_stream(json.dumps(data))
        self.assertEqual(parsed_str, data)

        self.assertEqual(self.classifier.parse_stream(None), {})
        self.assertEqual(self.classifier.parse_stream(""), {})

    async def test_process_activity_high_triggers_db_and_alert(self):
        mock_db = MagicMock()
        mock_db.save_market_activity = AsyncMock()

        mock_router = MagicMock()
        mock_router.dispatch_alert = AsyncMock()

        classifier = MarketActivityClassifier(db_storage=mock_db, alert_router=mock_router)

        trade_data = {"symbol": "ETH", "volume": 1000, "frequency": 100}
        hist_stats = {"avg_volume": 100, "avg_frequency": 10}

        significance = await classifier.process_activity(trade_data, hist_stats)

        self.assertEqual(significance, "High")
        mock_db.save_market_activity.assert_awaited_once()
        mock_router.dispatch_alert.assert_awaited_once()

        report = mock_db.save_market_activity.call_args[0][0]
        self.assertEqual(report["symbol"], "ETH")
        self.assertEqual(report["significance"], "High")
        self.assertEqual(report["deviation"], 10.0)

    async def test_process_activity_low_does_not_trigger_db_or_alert(self):
        mock_db = MagicMock()
        mock_db.save_market_activity = AsyncMock()

        mock_router = MagicMock()
        mock_router.dispatch_alert = AsyncMock()

        classifier = MarketActivityClassifier(db_storage=mock_db, alert_router=mock_router)

        trade_data = {"symbol": "ETH", "volume": 100, "frequency": 10}
        hist_stats = {"avg_volume": 100, "avg_frequency": 10}

        significance = await classifier.process_activity(trade_data, hist_stats)

        self.assertEqual(significance, "Low")
        mock_db.save_market_activity.assert_not_called()
        mock_router.dispatch_alert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
