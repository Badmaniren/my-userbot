import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_analyzer import market_portfolio_macro_liquidity_analyzer
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_valuation import market_portfolio_valuation

class TestMarketPortfolioMacroLiquidityAnalyzerIntegration(unittest.TestCase):
    def test_macro_liquidity_analyzer_integration(self):
        portfolio_id = str(uuid.uuid4())
        liquidity_threshold = round(random.uniform(10000.0, 1000000.0), 2)
        macro_factor = round(random.uniform(0.5, 2.0), 4)

        collector_data = {
            "portfolio_id": portfolio_id,
            "liquidity_threshold": liquidity_threshold,
            "macro_factor": macro_factor,
            "status": "initialized"
        }

        collector_result = market_portfolio_collector_agent(collector_data)
        self.assertIsNotNone(collector_result)

        valuation_result = market_portfolio_valuation(portfolio_id)
        self.assertIsNotNone(valuation_result)

        analyzer_input = {
            "portfolio_id": portfolio_id,
            "liquidity_threshold": liquidity_threshold,
            "macro_factor": macro_factor,
            "valuation_ref": valuation_result
        }

        analysis_output = market_portfolio_macro_liquidity_analyzer(analyzer_input)
        self.assertIsInstance(analysis_output, dict)
        self.assertEqual(analysis_output.get("portfolio_id"), portfolio_id)
        self.assertIn("liquidity_score", analysis_output)

        db_payload = {
            "id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "analysis": analysis_output
        }
        db_res = db_storage(db_payload)
        self.assertIsNotNone(db_res)

        test_file_path = f"macro_liquidity_{portfolio_id}.log"
        with open(test_file_path, "w") as f:
            f.write(str(analysis_output))

        self.assertTrue(os.path.exists(test_file_path))
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    unittest.main()