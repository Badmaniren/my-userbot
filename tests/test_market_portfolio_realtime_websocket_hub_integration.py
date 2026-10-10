import unittest
import uuid
import random
import os
from skills.market_portfolio_realtime_websocket_hub import (
    market_portfolio_realtime_websocket_hub,
    market_portfolio_realtime_stream_ingestor,
    market_portfolio_api_gateway,
    db_storage
)

class TestMarketPortfolioRealtimeWebsocketHubIntegration(unittest.TestCase):
    def test_websocket_hub_real_stream_integration(self):
        test_session_id = str(uuid.uuid4())
        test_ticker = f"ASSET_{random.randint(1000, 9999)}"
        test_price = round(random.uniform(10.0, 1500.0), 2)
        test_volume = random.randint(100, 50000)

        ingestor_payload = {
            "session_id": test_session_id,
            "ticker": test_ticker,
            "price": test_price,
            "volume": test_volume
        }

        ingest_result = market_portfolio_realtime_stream_ingestor(ingestor_payload)
        self.assertIsInstance(ingest_result, dict)
        self.assertIn("status", ingest_result)

        hub_payload = {
            "action": "subscribe",
            "session_id": test_session_id,
            "tickers": [test_ticker]
        }
        hub_response = market_portfolio_realtime_websocket_hub(hub_payload)
        self.assertIsInstance(hub_response, dict)
        self.assertEqual(hub_response.get("session_id"), test_session_id)
        self.assertIn(test_ticker, hub_response.get("active_subscriptions", []))

        gateway_payload = {
            "query_type": "latest_tick",
            "ticker": test_ticker
        }
        gateway_response = market_portfolio_api_gateway(gateway_payload)
        self.assertIsInstance(gateway_response, dict)
        self.assertEqual(gateway_response.get("ticker"), test_ticker)
        self.assertEqual(gateway_response.get("price"), test_price)

        db_check = db_storage({"action": "get_stream_log", "session_id": test_session_id})
        self.assertIsInstance(db_check, dict)
        self.assertEqual(db_check.get("stored_ticker"), test_ticker)

if __name__ == "__main__":
    unittest.main()