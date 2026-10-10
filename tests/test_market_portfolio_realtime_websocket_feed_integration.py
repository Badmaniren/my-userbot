import unittest
import uuid
import random
from skills.market_portfolio_realtime_websocket_feed import (
    market_portfolio_realtime_websocket_feed,
    start_new
)
from skills.market_portfolio_realtime_stream_analytics_hub import market_portfolio_realtime_stream_analytics_hub
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioRealtimeWebsocketFeed(unittest.TestCase):
    def test_realtime_feed_integration_pipeline(self):
        unique_feed_uuid = str(uuid.uuid4())
        random_symbol = f"SYM_{random.randint(1000, 9999)}"
        random_price = round(random.uniform(10.0, 1500.0), 2)
        random_volume = random.randint(100, 50000)

        payload = {
            "feed_uuid": unique_feed_uuid,
            "symbol": random_symbol,
            "price": random_price,
            "volume": random_volume
        }

        feed_result = market_portfolio_realtime_websocket_feed(payload)
        
        self.assertEqual(feed_result.get("status"), "connected")
        self.assertEqual(feed_result.get("feed_uuid"), unique_feed_uuid)
        self.assertEqual(feed_result.get("symbol"), random_symbol)
        self.assertEqual(feed_result.get("price"), random_price)
        self.assertEqual(feed_result.get("volume"), random_volume)

        analytics_payload = {
            "stream_id": unique_feed_uuid,
            "data": feed_result
        }
        
        if callable(market_portfolio_realtime_stream_analytics_hub):
            analytics_result = market_portfolio_realtime_stream_analytics_hub(analytics_payload)
            self.assertIsNotNone(analytics_result)

        tracking_id = f"track-{uuid.uuid4()}"
        start_result = start_new(tracking_id=tracking_id)
        self.assertEqual(start_result.get("tracking_id"), tracking_id)

        if callable(db_storage):
            db_payload = {
                "action": "save_feed_metrics",
                "feed_uuid": unique_feed_uuid,
                "symbol": random_symbol,
                "price": random_price
            }
            db_res = db_storage(db_payload)
            self.assertIsNotNone(db_res)

if __name__ == "__main__":
    unittest.main()