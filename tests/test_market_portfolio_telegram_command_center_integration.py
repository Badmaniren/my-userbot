import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_telegram_command_center import (
    MarketPortfolioTelegramCommandCenter,
    start_new
)
from skills.market_parser import MarketParser

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        
        self.symbol = f"TICK{random.randint(100, 999)}"
        self.test_prices = [round(random.uniform(10.0, 500.0), 2) for _ in range(5)]
        
        initial_data = {
            self.symbol: self.test_prices
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
            
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        self.chat_id = str(random.randint(100000, 999999))
        self.token = f"fake_token_{uuid.uuid4().hex}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_command_routing(self):
        cmd = "/start"
        response = self.command_center.handle_command(cmd, self.chat_id)
        self.assertIn("Welcome to Market Portfolio Telegram Command Center!", response)
        self.assertIn("/report", response)
        self.assertIn("/backtest", response)
        self.assertIn("/portfolio", response)

    def test_help_command_routing(self):
        cmd = "/help"
        response = self.command_center.process_command(cmd, self.chat_id)
        self.assertIn("Available commands:", response)

    def test_report_command_integration_with_parser_data(self):
        cmd = f"/report {self.symbol}"
        response = self.command_center.execute_command(cmd, self.chat_id)
        
        self.assertIn(f"Report for {self.symbol}", response)
        for price in self.test_prices:
            self.assertIn(str(price), response)

    def test_backtest_command_integration_with_parser_data(self):
        cmd = f"/backtest {self.symbol}"
        response = self.command_center.handle_command(cmd, self.chat_id)
        
        self.assertIn(f"Backtest executed for {self.symbol}", response)
        self.assertIn(f"Historical data points: {len(self.test_prices)}", response)

    def test_portfolio_command_summary(self):
        cmd = "/portfolio"
        response = self.command_center.handle_command(cmd, self.chat_id)
        self.assertIn("Portfolio summary", response)

    def test_unknown_command_handling(self):
        unknown_cmd = f"/unknown_{uuid.uuid4().hex[:6]}"
        response = self.command_center.handle_command(unknown_cmd, self.chat_id)
        self.assertIn("Unknown command", response)
        self.assertIn(unknown_cmd, response)

    def test_start_new_telegram_validation(self):
        res = start_new("", self.chat_id, "test message")
        self.assertFalse(res)
        
        res_empty = start_new(self.token, "", "")
        self.assertFalse(res_empty)

    def test_parser_file_persistence_integration(self):
        new_symbol = f"SYM{random.randint(1000, 9999)}"
        new_price = round(random.uniform(1.0, 100.0), 2)
        
        parser_instance = MarketParser(self.storage_file)
        if hasattr(parser_instance, 'fetch_and_store'):
            parser_instance.fetch_and_store(new_symbol, new_price)
        
        cmd = f"/report {new_symbol}"
        response = self.command_center.handle_command(cmd, self.chat_id)
        self.assertIn(new_symbol, response)
        self.assertIn(str(new_price), response)

if __name__ == '__main__':
    unittest.main()