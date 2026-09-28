import unittest
import os
import json
import tempfile
import uuid

from skills.market_portfolio_monitor import (
    MarketPortfolioMonitor,
    PortfolioMonitor,
    market_portfolio_monitor,
    calculate_drawdown,
    calculate_peak_to_trough,
    check_risk_limits,
    run_pipeline,
    start_new
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_monitor_{uuid.uuid4().hex}.json")
        self.monitor = MarketPortfolioMonitor(storage_file=self.storage_file, max_allowed_drawdown=0.15)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calculate_drawdown_empty_and_none(self):
        self.assertEqual(self.monitor.calculate_drawdown([]), 0.0)
        self.assertEqual(self.monitor.calculate_drawdown([None, None]), 0.0)

    def test_calculate_drawdown_increasing_prices(self):
        prices = [100.0, 105.0, 110.0, 115.0]
        dd = self.monitor.calculate_drawdown(prices)
        self.assertEqual(dd, 0.0)

    def test_calculate_drawdown_declining_prices(self):
        prices = [100.0, 90.0, 80.0]
        dd = self.monitor.calculate_drawdown(prices)
        self.assertAlmostEqual(dd, 0.20, places=4)

    def test_calculate_peak_to_trough(self):
        prices = [100.0, 120.0, 90.0, 110.0, 60.0, 80.0]
        result = self.monitor.calculate_peak_to_trough(prices)
        self.assertIn("max_drawdown", result)
        self.assertIn("peak", result)
        self.assertIn("trough", result)
        self.assertIn("drawdown_percentage", result)
        self.assertAlmostEqual(result["peak"], 120.0)
        self.assertAlmostEqual(result["trough"], 60.0)
        self.assertAlmostEqual(result["max_drawdown"], 0.50)
        self.assertAlmostEqual(result["drawdown_percentage"], 50.0)

    def test_calculate_peak_to_trough_empty(self):
        result = self.monitor.calculate_peak_to_trough([])
        self.assertEqual(result["max_drawdown"], 0.0)
        self.assertEqual(result["peak"], 0.0)
        self.assertEqual(result["trough"], 0.0)

    def test_check_risk_limits(self):
        # Within limit
        res_ok = self.monitor.check_risk_limits(0.10)
        self.assertFalse(res_ok["exceeded"])
        self.assertEqual(res_ok["status"], "OK")

        # Exceeded limit
        res_breach = self.monitor.check_risk_limits(0.25)
        self.assertTrue(res_breach["exceeded"])
        self.assertEqual(res_breach["status"], "BREACH")

        # Custom limit override
        res_custom = self.monitor.check_risk_limits(0.12, max_allowed=0.10)
        self.assertTrue(res_custom["exceeded"])

    def test_load_and_save_data(self):
        data = {"AAPL": [{"price": 150.0}, {"price": 140.0}]}
        saved = self.monitor.save_data(data)
        self.assertTrue(saved)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded = self.monitor.load_data()
        self.assertEqual(loaded, data)

    def test_load_data_missing_and_corrupt(self):
        # Missing file
        non_existent = os.path.join(self.temp_dir.name, "non_existent.json")
        loaded = self.monitor.load_data(non_existent)
        self.assertEqual(loaded, {})

        # Corrupt file
        corrupt_file = os.path.join(self.temp_dir.name, "corrupt.json")
        with open(corrupt_file, "w", encoding="utf-8") as f:
            f.write("NOT_VALID_JSON{")
        loaded_corrupt = self.monitor.load_data(corrupt_file)
        self.assertEqual(loaded_corrupt, {})

    def test_evaluate_portfolio_drawdown(self):
        # Dict with list of dicts
        symbol_data = [{"price": 100.0}, {"price": 120.0}, {"price": 90.0}]
        eval_res = self.monitor.evaluate_portfolio_drawdown(symbol_data, symbol="TEST")
        self.assertEqual(eval_res["symbol"], "TEST")
        self.assertAlmostEqual(eval_res["peak_to_trough"]["max_drawdown"], 0.25)

        # Dict payload
        dict_payload = {"prices": [100.0, 80.0]}
        eval_dict = self.monitor.evaluate_portfolio_drawdown(dict_payload, symbol="PAYLOAD")
        self.assertAlmostEqual(eval_dict["current_drawdown"], 0.20)

    def test_run_pipeline_creates_file(self):
        file_path = os.path.join(self.temp_dir.name, "new_pipeline_file.json")
        res = run_pipeline("MSFT", "http://test.url", "token123", "chat456", file_path)
        self.assertEqual(res["status"], "monitored")
        self.assertEqual(res["symbol"], "MSFT")
        self.assertTrue(os.path.exists(file_path))

    def test_start_new_function(self):
        res = start_new(symbol="TSLA", storage_file=self.storage_file)
        self.assertEqual(res["status"], "monitored")
        self.assertEqual(res["symbol"], "TSLA")

    def test_top_level_helpers(self):
        self.assertEqual(calculate_drawdown([100.0, 90.0]), 0.10)
        self.assertAlmostEqual(calculate_peak_to_trough([100.0, 50.0])["max_drawdown"], 0.50)
        self.assertTrue(check_risk_limits(0.30, max_allowed=0.20)["exceeded"])

    def test_aliases(self):
        self.assertEqual(PortfolioMonitor, MarketPortfolioMonitor)
        self.assertEqual(market_portfolio_monitor, MarketPortfolioMonitor)


if __name__ == "__main__":
    unittest.main()
