import unittest
import uuid
from skills.market_portfolio_realtime_websocket_gateway import (
    start_new,
    market_portfolio_realtime_websocket_gateway
)

class TestMarketPortfolioRealtimeWebsocketGatewayIntegration(unittest.TestCase):

    def test_start_new_and_gateway_flow_integration(self):
        deps = {
            "db_storage": f"db_{uuid.uuid4().hex}",
            "market_parser": f"parser_{uuid.uuid4().hex}"
        }
        res = start_new(**deps)
        self.assertIsInstance(res, dict)
        self.assertIn("token", res)
        self.assertIn("data", res)

        gateway = market_portfolio_realtime_websocket_gateway()
        stream_id = f"stream_{uuid.uuid4().hex}"
        symbol = f"TICKER_{uuid.uuid4().hex[:6]}"
        payload = {
            "stream_id": stream_id,
            "symbol": symbol,
            "price": 100.5,
            "volume": 500
        }

        routed_res = gateway.process_incoming_tick(payload)
        self.assertEqual(routed_res.get("status"), "routed")
        self.assertEqual(routed_res.get("stream_id"), stream_id)

if __name__ == "__main__":
    unittest.main()
