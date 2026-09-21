import unittest
import os
import uuid
import random
from skills.market_portfolio_websocket_bridge import MarketPortfolioWebsocketBridge, start_new
from skills.market_parser import MarketParser

class TestMarketPortfolioWebsocketBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.random_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_websocket_bridge_stream_and_emulation(self):
        bridge = MarketPortfolioWebsocketBridge(self.storage_file)

        connection_status = bridge.emulate_connection()
        self.assertTrue(connection_status)

        stream_output = bridge.stream_portfolio_updates(self.symbol)

        self.assertIn(str(self.symbol), stream_output)
        self.assertIn(str(self.random_price), stream_output)

    def test_start_new_streaming_loop(self):
        token = f"token_{uuid.uuid4()}"
        chat_id = str(random.randint(10000, 99999))
        dummy_url = f"http://localhost/{uuid.uuid4()}"

        try:
            start_new(
                symbol=self.symbol,
                url=dummy_url,
                telegram_token=token,
                chat_id=chat_id,
                storage_file=self.storage_file,
                max_iterations=1
            )
            success = True
        except Exception:
            success = False

        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()