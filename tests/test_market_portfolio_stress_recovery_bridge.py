import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills import market_portfolio_stress_recovery_bridge
from skills import market_portfolio_monitor
from skills import market_portfolio_stress_reporter

class TestMarketPortfolioStressRecoveryBridge(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AAF{uuid.uuid4().hex[:15]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.db"
        self.threshold = round(random.uniform(1.0, 15.0), 2)
        self.drop_limit = round(random.uniform(5.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 3) for _ in range(3)]

    def test_run_stress_recovery_pipeline(self):
        with patch('skills.market_portfolio_monitor.run_pipeline') as mock_monitor_run, \
             patch('skills.market_portfolio_stress_reporter.run_stress_reporting_pipeline') as mock_stress_run:

            mock_monitor_run.return_value = {"status": "monitor_ok"}
            mock_stress_run.return_value = {"status": "stress_ok"}

            result = market_portfolio_stress_recovery_bridge.run_stress_recovery_pipeline(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file, self.threshold
            )

            mock_monitor_run.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            mock_stress_run.assert_called_once()
            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("symbol"), self.symbol)

    def test_evaluate_and_recover(self):
        with patch('skills.market_portfolio_monitor.load_data') as mock_load, \
             patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_class, \
             patch('skills.market_portfolio_stress_reporter.generate_stress_report') as mock_gen_report, \
             patch('skills.market_portfolio_monitor.export_audit_logs') as mock_export:

            mock_reporter_instance = MagicMock()
            mock_reporter_class.return_value = mock_reporter_instance

            result = market_portfolio_stress_recovery_bridge.evaluate_and_recover(
                self.symbol, self.storage_file, self.drop_limit
            )

            mock_load.assert_called_once_with(self.storage_file)
            mock_reporter_class.assert_called_once_with(self.storage_file)
            mock_gen_report.assert_called_once_with(self.storage_file, self.symbol, self.drop_limit)
            mock_export.assert_called_once_with(self.storage_file)
            self.assertEqual(result.get("status"), "evaluated_and_recovered")
            self.assertEqual(result.get("symbol"), self.symbol)

    def test_trigger_recovery_protocols(self):
        expected_val = round(random.uniform(50.0, 500.0), 2)
        with patch('skills.market_portfolio_monitor.MarketParser') as mock_parser_class:
            mock_parser_instance = MagicMock()
            mock_parser_instance.fetch_and_store.return_value = expected_val
            mock_parser_class.return_value = mock_parser_instance

            result = market_portfolio_stress_recovery_bridge.trigger_recovery_protocols(
                self.symbol, self.storage_file
            )

            mock_parser_class.assert_called_once_with(self.storage_file)
            mock_parser_instance.fetch_and_store.assert_called_once_with(self.symbol, 100.0)
            self.assertEqual(result.get("status"), "triggered")
            self.assertEqual(result.get("value"), expected_val)

    def test_run_advanced_recovery_check(self):
        expected_res = {"status": "advanced_checked", "metric": random.randint(1, 100)}
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as mock_por_reporter_class:
            mock_por_instance = MagicMock()
            mock_por_instance.run_stress_report.return_value = expected_res
            mock_por_reporter_class.return_value = mock_por_instance

            result = market_portfolio_stress_recovery_bridge.run_advanced_recovery_check(
                self.symbol, self.shifts
            )

            mock_por_reporter_class.assert_called_once()
            mock_por_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_res)

    def test_safe_recovery_execution(self):
        expected_res = {"status": "safe_executed", "symbol": self.symbol}
        with patch('skills.market_portfolio_monitor.run_pipeline') as mock_run_pipeline:
            mock_run_pipeline.return_value = expected_res

            result = market_portfolio_stress_recovery_bridge.safe_recovery_execution(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )

            mock_run_pipeline.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            self.assertEqual(result, expected_res)

    def test_run_stress_recovery_bridge_pipeline_with_shifts(self):
        with patch('skills.market_portfolio_monitor.run_pipeline') as mock_monitor_run, \
             patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_class:

            mock_reporter_instance = MagicMock()
            mock_reporter_class.return_value = mock_reporter_instance

            result = market_portfolio_stress_recovery_bridge.run_stress_recovery_bridge_pipeline(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file, shifts=self.shifts
            )

            mock_monitor_run.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            mock_reporter_class.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result.get("status"), "bridge_pipeline_completed")
            self.assertEqual(result.get("symbol"), self.symbol)

    def test_run_stress_recovery_bridge_pipeline_without_shifts(self):
        with patch('skills.market_portfolio_monitor.run_pipeline') as mock_monitor_run, \
             patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_class, \
             patch('skills.market_portfolio_stress_reporter.run_stress_reporting_pipeline') as mock_default_stress_run:

            result = market_portfolio_stress_recovery_bridge.run_stress_recovery_bridge_pipeline(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file, shifts=None
            )

            mock_monitor_run.assert_called_once()
            mock_reporter_class.assert_called_once_with(self.storage_file)
            mock_default_stress_run.assert_called_once()
            self.assertEqual(result.get("status"), "bridge_pipeline_completed")

    def test_market_stress_recovery_bridge_methods(self):
        bridge = market_portfolio_stress_recovery_bridge.MarketStressRecoveryBridge(self.storage_file)
        self.assertEqual(bridge.storage_file, self.storage_file)
        self.assertEqual(bridge.execute_recovery(), {"status": "executed"})
        self.assertEqual(bridge.run_pipeline(), {"status": "pipeline_run"})