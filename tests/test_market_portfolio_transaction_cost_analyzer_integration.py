import unittest
import uuid
import random

from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics
from skills.market_portfolio_execution_cost_optimizer import market_portfolio_execution_cost_optimizer
from skills.market_parser import market_parser
from skills.market_anomaly_detector import market_anomaly_detector

from skills.market_portfolio_transaction_cost_analyzer import (
    market_portfolio_transaction_cost_analyzer,
    start_new
)

class TestMarketPortfolioTransactionCostAnalyzerIntegration(unittest.TestCase):

    def test_transaction_cost_analyzer_core_logic(self):
        portfolio_id = uuid.uuid4().hex
        ticker = f"TEST_{random.randint(1000, 9999)}"
        volume = round(random.uniform(100.0, 10000.0), 2)
        exchange_fee_rate = round(random.uniform(0.0001, 0.005), 5)

        estimated_slippage = round(random.uniform(0.0001, 0.002), 5)
        total_cost = volume * exchange_fee_rate
        slippage_metrics = {
            "estimated_slippage": estimated_slippage,
            "total_cost": total_cost
        }

        liquidity_data = {
            "depth": random.randint(50000, 500000),
            "spread": round(random.uniform(0.01, 0.1), 3)
        }

        result = market_portfolio_transaction_cost_analyzer(
            portfolio_id=portfolio_id,
            ticker=ticker,
            volume=volume,
            exchange_fee_rate=exchange_fee_rate,
            slippage_metrics=slippage_metrics,
            liquidity_data=liquidity_data
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("ticker"), ticker)
        self.assertEqual(result.get("volume"), volume)
        self.assertIn("total_transaction_cost", result)
        self.assertIn("impact_on_portfolio_return", result)
        self.assertIn("liquidity_info", result)

    def test_start_new_integration_with_real_deps(self):
        deps = {
            "db_storage": db_storage,
            "market_portfolio_execution_cost_optimizer": market_portfolio_execution_cost_optimizer,
            "market_parser": market_parser,
            "market_anomaly_detector": market_anomaly_detector,
            "market_portfolio_slippage_model": market_portfolio_slippage_model
        }

        res = start_new(deps)
        self.assertIsInstance(res, dict)
        self.assertIn("status", res)

    def test_start_new_invalid_deps_raises_type_error(self):
        with self.assertRaises(TypeError):
            start_new("not_a_dictionary")


if __name__ == "__main__":
    unittest.main()