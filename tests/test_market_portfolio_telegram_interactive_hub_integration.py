import unittest
import os
import uuid
import random
from skills.market_portfolio_telegram_interactive_hub import InteractiveTelegramHub
from skills.db_storage import MarketParser

class TestMarketPortfolioTelegramInteractiveHubIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 1500.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        self.hub = InteractiveTelegramHub(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_interactive_hub_status_and_simulation(self):
        chat_id = str(random.randint(100000, 999999))
        token = f"fake_token_{uuid.uuid4()}"

        status_result = self.hub.handle_command(chat_id, token, f"/status {self.symbol}")
        self.assertIsNotNone(status_result)
        self.assertIn(str(self.symbol), str(status_result))

        shift_value = random.randint(-20, 20)
        simulation_result = self.hub.handle_command(chat_id, token, f"/simulate {self.symbol} {shift_value}")
        self.assertIsNotNone(simulation_result)

        summary_result = self.hub.handle_command(chat_id, token, f"/summary {self.symbol}")
        self.assertIsNotNone(summary_result)

if __name__ == "__main__":
    unittest.main()