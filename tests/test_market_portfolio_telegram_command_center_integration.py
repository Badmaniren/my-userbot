import unittest
import os
import json
import uuid
import random
from skills.market_parser import MarketParser
from skills.market_portfolio_telegram_command_center import MarketPortfolioTelegramCommandCenter

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_data_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{random.randint(100, 999)}"
        self.prices = [round(random.uniform(10.0, 1000.0), 2) for _ in range(3)]
        
        data = {self.symbol: self.prices}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_command_center_integration_with_market_parser(self):
        chat_id = str(random.randint(10000, 99999))
        
        report_command = f"/report {self.symbol}"
        response = self.command_center.handle_command(report_command, chat_id)
        
        self.assertIn(self.symbol, response)
        for price in self.prices:
            self.assertIn(str(price), response)

        backtest_command = f"/backtest {self.symbol}"
        backtest_response = self.command_center.handle_command(backtest_command, chat_id)
        
        self.assertIn(self.symbol, backtest_response)
        self.assertIn(str(len(self.prices)), backtest_response)

        portfolio_response = self.command_center.handle_command("/portfolio", chat_id)
        self.assertIn("Portfolio summary", portfolio_response)

        help_response = self.command_center.handle_command("/start", chat_id)
        self.assertIn("Available commands", help_response)

        unknown_cmd = f"/unknown_{uuid.uuid4().hex[:6]}"
        unknown_response = self.command_center.handle_command(unknown_cmd, chat_id)
        self.assertIn("Unknown command", unknown_response)

if __name__ == '__main__':
    unittest.main()