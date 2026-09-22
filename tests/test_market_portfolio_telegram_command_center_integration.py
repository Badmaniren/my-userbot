import os
import json
import unittest
import uuid
import random
from skills.market_portfolio_telegram_command_center import MarketPortfolioTelegramCommandCenter
from skills.market_parser import MarketParser

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        
        self.symbol = f"TICK{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        
        initial_data = {
            self.symbol: [self.price, self.price * 1.05, self.price * 0.95]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)
            
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_report_command(self):
        chat_id = str(random.randint(10000, 99999))
        command = f"/report {self.symbol}"
        
        response = self.command_center.handle_command(command, chat_id)
        
        self.assertIn(self.symbol, response)
        self.assertIn(str(self.price), response)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_integration_backtest_command(self):
        chat_id = random.randint(10000, 99999)
        command = f"/backtest {self.symbol}"
        
        response = self.command_center.execute_command(command, chat_id)
        
        self.assertIn(self.symbol, response)
        self.assertIn("3", response)

    def test_integration_unknown_command(self):
        chat_id = str(random.randint(10000, 99999))
        random_cmd = f"/{uuid.uuid4().hex[:6]}"
        
        response = self.command_center.process_command(random_cmd, chat_id)
        
        self.assertIn("Unknown command", response)

if __name__ == "__main__":
    unittest.main()