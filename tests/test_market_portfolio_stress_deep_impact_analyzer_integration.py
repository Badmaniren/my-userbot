import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_deep_impact_analyzer import (
    market_portfolio_stress_deep_impact_analyzer
)
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class TestMarketPortfolioStressDeepImpactAnalyzerIntegration(unittest.TestCase):
    def test_deep_impact_analyzer_real_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_ticker = random.choice(["AAPL", "TSLA", "BTC", "ETH", "SPY", "QQQ"])
        initial_amount = round(random.uniform(50000.0, 1000000.0), 2)
        shock_magnitude = round(random.uniform(0.15, 0.65), 4)

        collector_input = {
            "portfolio_id": portfolio_id,
            "ticker": asset_ticker,
            "allocation": initial_amount,
            "timestamp": uuid.uuid4().int
        }
        collected_data = market_portfolio_collector_agent(collector_input)
        self.assertIsNotNone(collected_data)

        valuation_input = {
            "portfolio_id": portfolio_id,
            "market_data": collected_data
        }
        valuation_result = market_portfolio_valuation(valuation_input)
        self.assertIn("valuation", valuation_result)

        liquidity_input = {
            "portfolio_id": portfolio_id,
            "valuation_data": valuation_result,
            "stress_factor": shock_magnitude
        }
        liquidity_core_output = market_portfolio_var_liquidity_core(liquidity_input)
        self.assertIsInstance(liquidity_core_output, dict)

        analyzer_input = {
            "portfolio_id": portfolio_id,
            "liquidity_metrics": liquidity_core_output,
            "macro_shock_coefficient": shock_magnitude,
            "export_target_path": f"stress_report_{portfolio_id}.json"
        }

        result = market_portfolio_stress_deep_impact_analyzer(analyzer_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("cascade_liquidity_drain", result)
        self.assertIn("deep_impact_score", result)

        db_record = db_storage({
            "action": "get",
            "portfolio_id": portfolio_id,
            "table": "deep_impact_stress_logs"
        })
        self.assertIsNotNone(db_record)

        report_filename = analyzer_input["export_target_path"]
        self.assertTrue(os.path.exists(report_filename))

        if os.path.exists(report_filename):
            os.remove(report_filename)

if __name__ == "__main__":
    unittest.main()