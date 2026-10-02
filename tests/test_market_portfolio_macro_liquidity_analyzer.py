import unittest
from unittest.mock import MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_macro_liquidity_analyzer import (
    start_new,
    market_portfolio_macro_liquidity_analyzer,
    MarketPortfolioMacroLiquidityAnalyzer
)


class TestMarketPortfolioMacroLiquidityAnalyzer(unittest.TestCase):

    def setUp(self):
        self.random_db = uuid.uuid4().hex
        self.random_str_val = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.random_int_val = random.randint(1000, 99999)
        self.random_float_val = random.uniform(0.1, 999.9)

    def test_start_new_execution_flow(self):
        mock_db = MagicMock()
        mock_extractor_1 = MagicMock()
        mock_extractor_2 = MagicMock()
        mock_anomaly = MagicMock()

        dependencies = {
            "db_storage": mock_db,
            "extractor_tool_1790087207": mock_extractor_1,
            "extractor_tool_1790102839": mock_extractor_2,
            "market_anomaly_detector": mock_anomaly,
        }

        mock_extractor_1.return_value = self.random_str_val
        mock_anomaly.return_value = self.random_int_val

        byte_stream_data = io.BytesIO(self.random_str_val.encode('utf-8'))

        res = start_new(dependencies, liquidity_threshold=self.random_float_val, stream=byte_stream_data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

        mock_extractor_1.assert_called_once()
        mock_extractor_2.assert_called_once()
        mock_anomaly.assert_called_once()

    def test_start_new_stream_handling(self):
        mock_dep = {
            "db_storage": uuid.uuid4().hex,
            "extractor_tool_1790087207": uuid.uuid4().hex
        }
        random_bytes = io.BytesIO(uuid.uuid4().bytes)

        res = start_new(mock_dep, input_stream=random_bytes)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

    def test_start_new_exception_resilience(self):
        faulty_dependency_map = {
            key: None for key in [
                "db_storage", "extractor_tool_1790087207", "extractor_tool_1790102839",
                "market_anomaly_detector"
            ]
        }

        res = start_new(faulty_dependency_map)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

    def test_market_portfolio_macro_liquidity_analyzer_function(self):
        portfolio_id = str(uuid.uuid4())
        data = {
            "portfolio_id": portfolio_id,
            "liquidity_threshold": 100000.0,
            "macro_factor": 1.5,
            "valuation_ref": {"valuation": 80000.0}
        }

        res = market_portfolio_macro_liquidity_analyzer(data)
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["liquidity_score"], 120000.0)
        self.assertTrue(res["is_liquid"])

        # Test with float valuation_ref and invalid macro factor
        res2 = market_portfolio_macro_liquidity_analyzer(
            portfolio_id=portfolio_id,
            liquidity_threshold=100000.0,
            macro_factor="invalid",
            valuation_ref=50000.0
        )
        self.assertEqual(res2["liquidity_score"], 50000.0)
        self.assertFalse(res2["is_liquid"])

        # Test non-dict default
        res3 = market_portfolio_macro_liquidity_analyzer(None)
        self.assertEqual(res3["portfolio_id"], "default_portfolio")

    def test_class_analyzer(self):
        analyzer = MarketPortfolioMacroLiquidityAnalyzer(default_threshold=5000.0, default_macro_factor=1.2)
        data = {
            "portfolio_id": "test_class_portfolio",
            "liquidity_threshold": 50000.0,
            "macro_factor": 1.2,
            "valuation_ref": 60000.0
        }
        res1 = analyzer.evaluate_liquidity(data)
        self.assertEqual(res1["portfolio_id"], "test_class_portfolio")
        self.assertEqual(res1["liquidity_score"], 72000.0)
        self.assertTrue(res1["is_liquid"])

        res2 = analyzer.analyze(data)
        self.assertEqual(res2, res1)


if __name__ == "__main__":
    unittest.main()
