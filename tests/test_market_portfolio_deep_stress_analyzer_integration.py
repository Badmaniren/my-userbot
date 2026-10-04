import unittest
import uuid
import random
import os
from skills.market_portfolio_deep_stress_analyzer import market_portfolio_deep_stress_analyzer
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.db_storage import db_storage

class TestMarketPortfolioDeepStressAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.asset_ticker = f"TICK_{random.randint(1000, 9999)}"
        self.initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        self.stress_drop_pct = round(random.uniform(10.0, 45.0), 2)

    def test_deep_stress_analyzer_end_to_end_integration(self):
        collector_input = {
            "portfolio_id": self.portfolio_id,
            "ticker": self.asset_ticker,
            "volume": random.randint(100, 5000),
            "price": round(random.uniform(10.0, 500.0), 2)
        }
        collected_data = market_portfolio_collector_agent(collector_input)
        self.assertIsNotNone(collected_data)

        valuation_input = {
            "portfolio_id": self.portfolio_id,
            "capital": self.initial_capital
        }
        valuation_result = market_portfolio_valuation(valuation_input)
        self.assertIn("portfolio_id", valuation_result)

        liquidity_input = {
            "portfolio_id": self.portfolio_id,
            "volatility_index": round(random.uniform(1.1, 4.5), 4)
        }
        liquidity_metrics = market_portfolio_liquidity_scenario_analyzer(liquidity_input)
        self.assertIsInstance(liquidity_metrics, dict)

        stress_input = {
            "portfolio_id": self.portfolio_id,
            "historical_drop_pct": self.stress_drop_pct,
            "liquidity_data": liquidity_metrics,
            "valuation_data": valuation_result
        }
        stress_analysis_output = market_portfolio_deep_stress_analyzer(stress_input)

        self.assertIsInstance(stress_analysis_output, dict)
        self.assertIn("stress_score", stress_analysis_output)
        self.assertIn("max_drawdown", stress_analysis_output)
        self.assertEqual(stress_analysis_output["portfolio_id"], self.portfolio_id)

        db_payload = {
            "id": f"stress_res_{uuid.uuid4().hex}",
            "portfolio_id": self.portfolio_id,
            "score": stress_analysis_output["stress_score"]
        }
        db_save_result = db_storage(db_payload)
        self.assertTrue(db_save_result)

if __name__ == "__main__":
    unittest.main()