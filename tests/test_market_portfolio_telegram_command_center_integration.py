import unittest
import os
import json
import uuid
from skills.market_parser import MarketParser
from skills.market_portfolio_telegram_command_center import MarketPortfolioTelegramCommandCenter

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{uuid.uuid4().hex[:4].upper()}"
        self.test_prices = [100.5, 102.0, 101.2, 105.0]
        
        data = {
            self.symbol: self.test_prices
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_report_command(self):
        chat_id = str(uuid.uuid4())
        command = f"/report {self.symbol}"
        
        response = self.command_center.handle_command(command, chat_id)
        
        self.assertIn(self.symbol, response)
        for price in self.test_prices:
            self.assertIn(str(price), response)

    def test_integration_backtest_command(self):
        chat_id = str(uuid.uuid4())
        command = f"/backtest {self.symbol}"
        
        response = self.command_center.handle_command(command, chat_id)
        
        self.assertIn(self.symbol, response)
        self.assertIn(str(len(self.test_prices)), response)

    def test_integration_portfolio_command(self):
        chat_id = str(uuid.uuid4())
        command = "/portfolio"
        
        response = self.command_center.handle_command(command, chat_id)
        
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

if __name__ == '__main__':
    unittest.main()