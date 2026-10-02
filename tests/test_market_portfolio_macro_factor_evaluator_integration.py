import unittest
import uuid
import random
from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_macro_factor_evaluator import market_portfolio_macro_factor_evaluator, start_new

class TestMarketPortfolioMacroFactorEvaluatorIntegration(unittest.TestCase):

    def test_macro_factor_evaluation_and_start_new_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        inflation = round(random.uniform(1.0, 10.0), 2)
        interest_rate = round(random.uniform(0.5, 15.0), 2)
        gdp_growth = round(random.uniform(-3.0, 5.0), 2)

        eval_result = market_portfolio_macro_factor_evaluator.evaluate(
            portfolio_id=portfolio_id,
            inflation=inflation,
            interest_rate=interest_rate,
            gdp_growth=gdp_growth
        )

        self.assertIn("evaluation_id", eval_result)
        self.assertEqual(eval_result["portfolio_id"], portfolio_id)
        self.assertEqual(eval_result["inflation"], inflation)
        self.assertEqual(eval_result["interest_rate"], interest_rate)
        self.assertEqual(eval_result["gdp_growth"], gdp_growth)
        self.assertEqual(eval_result["status"], "evaluated")

        eval_id = eval_result["evaluation_id"]
        stored_record = db_storage.get_record(eval_id) if hasattr(db_storage, "get_record") else None
        if stored_record:
            self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)

        start_result = start_new(
            db_storage=db_storage,
            market_parser=market_parser,
            market_portfolio_scenario_simulator=market_portfolio_scenario_simulator
        )

        self.assertIsInstance(start_result, dict)
        self.assertIn("status", start_result)

if __name__ == "__main__":
    unittest.main()