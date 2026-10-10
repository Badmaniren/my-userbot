import unittest
import uuid
import random
import os
from skills.market_portfolio_realtime_websocket_gateway_v2 import market_portfolio_realtime_websocket_gateway_v2
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.db_storage import db_storage

class TestMarketPortfolioRealtimeWebsocketGatewayV2Integration(unittest.TestCase):
    def test_websocket_gateway_real_flow(self):
        unique_symbol = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        random_price = round(random.uniform(10.0, 1500.0), 2)
        random_volume = random.randint(100, 10000)

        collector_input = {
            "symbol": unique_symbol,
            "price": random_price,
            "volume": random_volume,
            "source": "integration_test"
        }

        try:
            collector_result = market_portfolio_collector_agent(collector_input)
        except Exception as e:
            self.fail(f"Collector agent failed during integration: {e}")

        gateway_payload = {
            "action": "stream_quote",
            "data": collector_result if isinstance(collector_result, dict) else collector_input
        }

        try:
            gateway_response = market_portfolio_realtime_websocket_gateway_v2(gateway_payload)
        except Exception as e:
            self.fail(f"Websocket gateway v2 raised an exception: {e}")

        self.assertIsNotNone(gateway_response, "Gateway response cannot be None")
        
        if isinstance(gateway_response, dict):
            self.assertIn("status", gateway_response)
            self.assertEqual(gateway_response["status"], "success")

        db_query = {
            "filter": {"symbol": unique_symbol},
            "limit": 1
        }
        
        try:
            db_records = db_storage(db_query)
        except Exception as e:
            self.fail(f"Database storage retrieval failed: {e}")

        self.assertIsInstance(db_records, list)
        self.assertTrue(len(db_records) > 0, "No records found in database storage after gateway processing")
        
        stored_record = db_records[0]
        self.assertEqual(stored_record.get("symbol"), unique_symbol)
        self.assertEqual(stored_record.get("price"), random_price)

if __name__ == "__main__":
    unittest.main()