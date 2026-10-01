import unittest
from unittest.mock import patch
import uuid
import random
import io
import os

from skills.market_portfolio_var_liquidity_adjusted_calculator import (
    MarketPortfolioVarLiquidityAdjustedCalculator,
    market_portfolio_var_liquidity_adjusted_calculator
)


class TestMarketPortfolioVarLiquidityAdjustedCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.calculator = MarketPortfolioVarLiquidityAdjustedCalculator()

    def test_init_default(self):
        calc = MarketPortfolioVarLiquidityAdjustedCalculator()
        self.assertIsNone(calc.db_storage)
        self.assertIsNone(calc.extractor_tool)
        self.assertIsNone(calc.market_anomaly_detector)

    def test_fetch_market_depth_default(self):
        res = self.calculator._fetch_market_depth(self.portfolio_id)
        self.assertIsInstance(res, dict)
        self.assertIn("depth", res)
        self.assertIn("volatility", res)
        self.assertIn("spread", res)

    def test_fetch_market_depth_with_extractor(self):
        mock_extractor = unittest.mock.MagicMock()
        expected_dict = {
            "depth": random.randint(1000, 500000),
            "volatility": random.uniform(0.01, 0.1),
            "spread": random.uniform(0.0001, 0.01)
        }
        mock_extractor.fetch.return_value = expected_dict
        calc = MarketPortfolioVarLiquidityAdjustedCalculator(extractor_tool_1790087207=mock_extractor)
        res = calc._fetch_market_depth(self.portfolio_id)
        self.assertEqual(res, expected_dict)
        mock_extractor.fetch.assert_called_once_with(self.portfolio_id)

    def test_compute_lvar_basic(self):
        confidence = round(random.uniform(0.9, 0.99), 2)
        horizon = random.randint(1, 10)
        res = self.calculator.compute_lvar(self.portfolio_id, confidence_level=confidence, time_horizon_days=horizon)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["confidence_level"], confidence)
        self.assertEqual(res["time_horizon_days"], horizon)
        self.assertIn("lvar", res)
        self.assertGreaterEqual(res["lvar"], 0.0)

    def test_compute_lvar_with_anomaly_detector(self):
        mock_detector = unittest.mock.MagicMock()
        calc = MarketPortfolioVarLiquidityAdjustedCalculator(market_anomaly_detector=mock_detector)
        calc.compute_lvar(self.portfolio_id)
        mock_detector.check_anomaly.assert_called_once_with(self.portfolio_id)

    def test_estimate_liquidity_cost(self):
        vol = random.uniform(500000.0, 2000000.0)
        spread = random.uniform(0.001, 0.05)
        content = f"volume:{vol},spread:{spread}"
        stream_path = f"{uuid.uuid4().hex}.txt"

        with patch("builtins.open", unittest.mock.mock_open(read_data=content)):
            pos_size = random.uniform(1000.0, 100000.0)
            cost = self.calculator.estimate_liquidity_cost(pos_size, stream_path)
            self.assertIsInstance(cost, float)
            self.assertGreaterEqual(cost, 0.0)

    def test_estimate_liquidity_cost_bad_parsing(self):
        content = f"volume:not_a_number,spread:0.01"
        stream_path = f"{uuid.uuid4().hex}.txt"

        with patch("builtins.open", unittest.mock.mock_open(read_data=content)):
            with self.assertRaises(ValueError):
                self.calculator.estimate_liquidity_cost(1000.0, stream_path)

    def test_persist_lvar_result(self):
        mock_db = unittest.mock.MagicMock()
        calc = MarketPortfolioVarLiquidityAdjustedCalculator(db_storage=mock_db)
        lvar_val = random.uniform(100.0, 50000.0)
        calc.persist_lvar_result(self.portfolio_id, lvar_val)
        mock_db.save_metric.assert_called_once_with(self.portfolio_id, lvar_val)

    def test_functional_wrapper(self):
        valuation_dict = {"valuation": random.uniform(1000.0, 100000.0)}
        slippage_dict = {"slippage": random.uniform(1.0, 500.0)}
        conf = round(random.uniform(0.9, 0.99), 2)
        period = random.randint(1, 5)

        output_filepath = f"report_{self.portfolio_id}.json"
        if os.path.exists(output_filepath):
            os.remove(output_filepath)

        try:
            res = market_portfolio_var_liquidity_adjusted_calculator(
                portfolio_id=self.portfolio_id,
                valuation=valuation_dict,
                slippage=slippage_dict,
                confidence_level=conf,
                holding_period_days=period
            )
            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["confidence_level"], conf)
            self.assertEqual(res["holding_period_days"], period)
            self.assertTrue(res["persisted"])
            self.assertIn("l_var_value", res)
            self.assertTrue(os.path.exists(output_filepath))
        finally:
            if os.path.exists(output_filepath):
                os.remove(output_filepath)