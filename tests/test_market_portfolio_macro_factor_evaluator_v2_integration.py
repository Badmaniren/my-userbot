import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_factor_evaluator_v2 import evaluate_macro_factors
from skills.db_storage import save_evaluation_result, get_evaluation_result

class TestMarketPortfolioMacroFactorEvaluatorV2Integration(unittest.TestCase):

    def test_macro_factor_evaluator_integration_flow(self):
        unique_portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        random_gdp_growth = round(random.uniform(-3.5, 5.0), 2)
        random_inflation_rate = round(random.uniform(0.5, 12.0), 2)
        random_interest_rate = round(random.uniform(0.0, 8.5), 2)

        evaluation_input = {
            "portfolio_id": unique_portfolio_id,
            "gdp_growth": random_gdp_growth,
            "inflation_rate": random_inflation_rate,
            "interest_rate": random_interest_rate
        }

        result = evaluate_macro_factors(evaluation_input)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], unique_portfolio_id)
        self.assertIn("macro_score", result)

        db_record_id = f"rec_{uuid.uuid4().hex}"
        save_evaluation_result(db_record_id, result)

        fetched_data = get_evaluation_result(db_record_id)
        self.assertIsNotNone(fetched_data)
        self.assertEqual(fetched_data["portfolio_id"], unique_portfolio_id)
        self.assertEqual(fetched_data["gdp_growth"], random_gdp_growth)
        self.assertEqual(fetched_data["inflation_rate"], random_inflation_rate)
        self.assertEqual(fetched_data["interest_rate"], random_interest_rate)

if __name__ == "__main__":
    unittest.main()