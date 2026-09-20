import unittest
import os
import uuid
import random
from skills.market_portfolio_websocket_bridge import MarketPortfolioWebsocketBridge
from skills.market_parser import MarketParser

class TestMarketPortfolioWebsocketBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.initial_price = round(random.uniform(10.0, 500.0), 2)
        
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.initial_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_websocket_bridge_stream_integration(self):
        bridge = MarketPortfolioWebsocketBridge(self.storage_file)
        
        self.assertTrue(
            hasattr(bridge, "stream_portfolio_updates") or hasattr(bridge, "emulate_connection") or hasattr(bridge, "run_bridge"),
            "Bridge module must expose streaming or connection emulation methods."
        )

        if hasattr(bridge, "emulate_connection"):
            connection_status = bridge.emulate_connection()
            self.assertIsNotNone(connection_status)

        if hasattr(bridge, "stream_portfolio_updates"):
            new_price = round(random.uniform(501.0, 1000.0), 2)
            parser = MarketParser(self.storage_file)
            parser.fetch_and_store(self.symbol, new_price)
            
            stream_data = bridge.stream_portfolio_updates(self.symbol)
            self.assertIn(self.symbol, str(stream_data))
            self.assertIn(str(new_price), str(stream_data))

if __name__ == "__main__":
    unittest.main()