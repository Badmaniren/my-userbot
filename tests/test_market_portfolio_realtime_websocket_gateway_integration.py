import unittest
import uuid
import random
import os
import time

from skills.market_portfolio_realtime_websocket_gateway import market_portfolio_realtime_websocket_gateway
from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor
from skills.db_storage import db_storage


class TestMarketPortfolioRealtimeWebsocketGatewayIntegration(unittest.TestCase):

    def setUp(self):
        self.gateway = market_portfolio_realtime_websocket_gateway()
        self.ingestor = market_portfolio_realtime_stream_ingestor()
        self.storage = db_storage()
        
        self.test_stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        self.test_symbol = f"ASSET_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 1500.0), 4)
        self.test_volume = round(random.uniform(0.1, 500.0), 2)

    def test_websocket_gateway_to_ingestor_integration(self):
        payload = {
            "stream_id": self.test_stream_id,
            "symbol": self.test_symbol,
            "price": self.test_price,
            "volume": self.test_volume,
            "timestamp": time.time_ns()
        }

        gateway_result = self.gateway.process_incoming_tick(payload)
        self.assertIsNotNone(gateway_result)
        self.assertEqual(gateway_result.get("status"), "routed")
        self.assertEqual(gateway_result.get("stream_id"), self.test_stream_id)

        ingested_data = self.ingestor.consume_stream_data(self.test_stream_id)
        self.assertIsNotNone(ingested_data)
        self.assertEqual(ingested_data.get("symbol"), self.test_symbol)
        self.assertEqual(ingested_data.get("price"), self.test_price)
        self.assertEqual(ingested_data.get("volume"), self.test_volume)

        persisted_record = self.storage.get_latest_tick(self.test_symbol)
        self.assertIsNotNone(persisted_record)
        self.assertEqual(persisted_record.get("price"), self.test_price)

    def tearDown(self):
        if hasattr(self.storage, "cleanup_test_data"):
            self.storage.cleanup_test_data(self.test_symbol)


if __name__ == "__main__":
    unittest.main()