import unittest
import uuid
import random
import asyncio
from skills.market_portfolio_realtime_websocket_feed import market_portfolio_realtime_websocket_feed
from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioRealtimeWebsocketFeed(unittest.TestCase):
    def setUp(self):
        self.feed_id = str(uuid.uuid4())
        self.test_symbol = f"TEST_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 1500.0), 2)

    def test_websocket_feed_integration_pipeline(self):
        payload = {
            "feed_uuid": self.feed_id,
            "symbol": self.test_symbol,
            "price": self.test_price,
            "volume": random.randint(100, 10000)
        }

        feed_result = market_portfolio_realtime_websocket_feed(payload)
        
        self.assertIsInstance(feed_result, dict)
        self.assertIn("status", feed_result)
        self.assertEqual(feed_result.get("feed_uuid"), self.feed_id)

        ingestor_payload = {
            "source_feed": feed_result,
            "routing_key": self.test_symbol
        }
        ingestor_result = market_portfolio_realtime_stream_ingestor(ingestor_payload)
        
        self.assertIsInstance(ingestor_result, dict)
        self.assertEqual(ingestor_result.get("symbol"), self.test_symbol)

        db_payload = {
            "query_type": "insert_feed_data",
            "record_id": self.feed_id,
            "data": ingestor_result
        }
        db_result = db_storage(db_payload)

        self.assertIsInstance(db_result, dict)
        self.assertEqual(db_result.get("record_id"), self.feed_id)
        self.assertEqual(db_result.get("stored_status"), "SUCCESS")

if __name__ == "__main__":
    unittest.main()