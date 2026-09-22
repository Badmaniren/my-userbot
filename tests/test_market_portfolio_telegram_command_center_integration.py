import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_telegram_command_center import MarketPortfolioTelegramCommandCenter, start_new
from skills.market_parser import MarketParser

class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.unique_suffix}.json"
        self.symbol = f"TICK{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        
        self.parser = MarketParser(self.storage_file)
        self.parser.fetch_and_store(self.symbol, self.price)
        
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_workflow_and_commands(self):
        self.assertTrue(os.path.exists(self.storage_file), "Интеграционный тест требует реального файла хранилища")
        
        help_response = self.command_center.handle_command("/start", self.chat_id)
        self.assertIn("Welcome to Market Portfolio Telegram Command Center", help_response)
        
        report_command = f"/report {self.symbol}"
        report_response = self.command_center.handle_command(report_command, self.chat_id)
        self.assertIn(f"Report for {self.symbol}", report_response)
        self.assertIn(str(self.price), report_response)
        
        backtest_command = f"/backtest {self.symbol}"
        backtest_response = self.command_center.handle_command(backtest_command, self.chat_id)
        self.assertIn(f"Backtest executed for {self.symbol}", backtest_response)
        
        portfolio_response = self.command_center.execute_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary", portfolio_response)
        
        unknown_response = self.command_center.process_command(f"/unknown_{self.unique_suffix}", self.chat_id)
        self.assertIn("Unknown command", unknown_response)
        
        dummy_token = f"fake_token_{uuid.uuid4().hex}"
        send_result = start_new(dummy_token, self.chat_id, f"Integration test message {self.unique_suffix}")
        self.assertFalse(send_result)

if __name__ == "__main__":
    unittest.main()