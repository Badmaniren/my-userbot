import os
import json
import unittest
import uuid
import random
from skills.market_portfolio_telegram_command_center import MarketPortfolioTelegramCommandCenter
from skills.market_parser import MarketParser

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        
        initial_data = {
            self.symbol: [self.price, self.price * 1.05]
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
            
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_command_processing_and_market_parser(self):
        command = f"/report {self.symbol}"
        response = self.command_center.handle_command(command, self.chat_id)
        
        self.assertIsInstance(response, str)
        self.assertIn(self.symbol, response)
        self.assertIn(str(self.price), response)

    def test_integration_backtest_command(self):
        command = f"/backtest {self.symbol}"
        response = self.command_center.execute_command(command, self.chat_id)
        
        self.assertIsInstance(response, str)
        self.assertIn(self.symbol, response)
        self.assertIn("Backtest executed", response)

    def test_integration_unknown_and_help_commands(self):
        help_response = self.command_center.process_command("/start", self.chat_id)
        self.assertIn("Welcome to Market Portfolio Telegram Command Center", help_response)
        
        random_cmd = f"/unknown_{uuid.uuid4().hex[:6]}"
        unknown_response = self.command_center.handle_command(random_cmd, self.chat_id)
        self.assertIn("Unknown command", unknown_response)

if __name__ == "__main__":
    unittest.main()