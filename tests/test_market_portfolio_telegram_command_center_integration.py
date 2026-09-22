import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_telegram_command_center import MarketPortfolioTelegramCommandCenter
from skills.market_parser import MarketParser

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.unique_suffix}.json"
        
        self.symbol = f"TICK{random.randint(100, 999)}"
        self.test_prices = [round(random.uniform(10.0, 500.0), 2) for _ in range(5)]
        
        initial_data = {
            self.symbol: self.test_prices
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
            
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        self.chat_id = str(random.randint(10000, 99999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_handle_command_report_integration(self):
        command = f"/report {self.symbol}"
        response = self.command_center.handle_command(command, self.chat_id)
        
        self.assertIn(self.symbol, response)
        for price in self.test_prices:
            self.assertIn(str(price), response)

    def test_handle_command_backtest_integration(self):
        command = f"/backtest {self.symbol}"
        response = self.command_center.handle_command(command, self.chat_id)
        
        self.assertIn(self.symbol, response)
        self.assertIn(str(len(self.test_prices)), response)

    def test_handle_command_portfolio_integration(self):
        command = "/portfolio"
        response = self.command_center.handle_command(command, self.chat_id)
        
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_market_parser_interaction_directly(self):
        parser = MarketParser(self.storage_file)
        loaded_data = {}
        if hasattr(parser, 'load_data'):
            try:
                loaded_data = parser.load_data(self.storage_file)
            except TypeError:
                loaded_data = parser.load_data()
                
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.test_prices)

if __name__ == '__main__':
    unittest.main()