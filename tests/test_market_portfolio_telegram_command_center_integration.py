import json
import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.market_parser import MarketParser
import skills.market_portfolio_telegram_command_center as command_center_module


class TestMarketPortfolioTelegramCommandCenterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tg_cmd_center_test_")
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")

        self.cls = getattr(
            command_center_module,
            "MarketPortfolioTelegramCommandCenter",
            getattr(command_center_module, "TelegramCommandCenter", None),
        )
        if self.cls is None:
            self.fail(
                "Neither MarketPortfolioTelegramCommandCenter nor TelegramCommandCenter "
                "found in skills.market_portfolio_telegram_command_center"
            )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _execute_command(self, center, command, chat_id):
        for method_name in ("handle_command", "process_command", "execute_command"):
            if hasattr(center, method_name):
                return getattr(center, method_name)(command, chat_id)
        self.fail("Command center must implement handle_command, process_command, or execute_command")

    def test_end_to_end_telegram_commands_workflow(self):
        symbol_a = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        symbol_b = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        chat_id = random.randint(1000000, 9999999)

        prices_a = [round(random.uniform(100.0, 150.0), 2) for _ in range(4)]
        prices_b = [round(random.uniform(20.0, 40.0), 2) for _ in range(4)]

        parser = MarketParser(self.storage_file)
        for p in prices_a:
            parser.fetch_and_store(symbol_a, p)
        for p in prices_b:
            parser.fetch_and_store(symbol_b, p)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by MarketParser")
        self.assertGreater(os.path.getsize(self.storage_file), 0, "Storage file must contain recorded prices")

        center = self.cls(self.storage_file)

        help_response = self._execute_command(center, "/start", chat_id)
        help_str = json.dumps(help_response) if isinstance(help_response, dict) else str(help_response)
        self.assertTrue(
            any(kw in help_str.lower() for kw in ["report", "backtest", "portfolio", "help", "command"]),
            f"Start/help response must list capabilities: {help_str}",
        )

        report_a = self._execute_command(center, f"/report {symbol_a}", chat_id)
        report_a_str = json.dumps(report_a) if isinstance(report_a, dict) else str(report_a)
        self.assertIn(symbol_a, report_a_str, f"Report must reference requested symbol {symbol_a}")
        self.assertNotIn(symbol_b, report_a_str, f"Report for {symbol_a} must not include {symbol_b}")

        report_b = self._execute_command(center, f"/report {symbol_b}", chat_id)
        report_b_str = json.dumps(report_b) if isinstance(report_b, dict) else str(report_b)
        self.assertIn(symbol_b, report_b_str, f"Report must reference requested symbol {symbol_b}")
        self.assertNotIn(symbol_a, report_b_str, f"Report for {symbol_b} must not include {symbol_a}")

        backtest_a = self._execute_command(center, f"/backtest {symbol_a}", chat_id)
        bt_a_str = json.dumps(backtest_a) if isinstance(backtest_a, dict) else str(backtest_a)
        self.assertIn(symbol_a, bt_a_str, f"Backtest response must contain target symbol {symbol_a}")


if __name__ == "__main__":
    unittest.main()