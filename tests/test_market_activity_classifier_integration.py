import unittest
from unittest.mock import AsyncMock, MagicMock
import io
import json
import uuid
import random

from skills.market_activity_classifier import MarketActivityClassifier


class TestMarketActivityClassifierIntegration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_db.save_market_activity = AsyncMock()

        self.mock_router = MagicMock()
        self.mock_router.dispatch_alert = AsyncMock()

        self.classifier = MarketActivityClassifier(
            high_threshold=4.0,
            medium_threshold=2.0,
            db_storage=self.mock_db,
            alert_router=self.mock_router
        )

    async def test_end_to_end_stream_processing_pipeline(self):
        unique_symbol = f"SYM_{uuid.uuid4().hex[:6]}"

        # High volume anomaly trade
        raw_stream_data = {
            "symbol": unique_symbol,
            "volume": 5000,
            "frequency": 20
        }

        stream = io.BytesIO(json.dumps(raw_stream_data).encode('utf-8'))

        # 1. Parse stream
        trade_data = self.classifier.parse_stream(stream)
        self.assertEqual(trade_data["symbol"], unique_symbol)

        # 2. Historical baseline stats
        historical_stats = {
            "avg_volume": 1000,
            "avg_frequency": 10
        }

        # 3. Process activity
        significance = await self.classifier.process_activity(trade_data, historical_stats)

        # Deviation = max(5000/1000, 20/10) = 5.0 >= 4.0 threshold -> "High"
        self.assertEqual(significance, "High")

        self.mock_db.save_market_activity.assert_awaited_once()
        self.mock_router.dispatch_alert.assert_awaited_once()

        saved_report = self.mock_db.save_market_activity.call_args[0][0]
        self.assertEqual(saved_report["symbol"], unique_symbol)
        self.assertEqual(saved_report["significance"], "High")
        self.assertEqual(saved_report["deviation"], 5.0)

    async def test_batch_stream_classification_integration(self):
        trades = [
            {"symbol": "AAA", "volume": 100, "frequency": 10},  # Low (1.0)
            {"symbol": "BBB", "volume": 250, "frequency": 10},  # Medium (2.5)
            {"symbol": "CCC", "volume": 500, "frequency": 10},  # High (5.0)
        ]

        historical_stats = {"avg_volume": 100, "avg_frequency": 10}

        results = []
        for trade in trades:
            res = await self.classifier.process_activity(trade, historical_stats)
            results.append(res)

        self.assertEqual(results, ["Low", "Medium", "High"])
        self.assertEqual(self.mock_db.save_market_activity.await_count, 1)
        self.assertEqual(self.mock_router.dispatch_alert.await_count, 1)


if __name__ == "__main__":
    unittest.main()
