import unittest
import uuid
import random
from skills.market_portfolio_macro_factor_evaluator import start_new, evaluate_macro_factors
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_parser import fetch_market_indicators
from skills.db_storage import save_macro_evaluation, get_macro_evaluation

class IntegrationTestMarketPortfolioMacroFactorEvaluator(unittest.TestCase):

    def test_macro_factor_evaluation_integration(self):
        random_portfolio_id = str(uuid.uuid4())
        random_impact_base = round(random.uniform(0.1, 0.9), 2)

        mock_portfolio_data = {
            "portfolio_id": random_portfolio_id,
            "assets": ["AAPL", "GOOGL", "MSFT"],
            "valuation": random.randint(10000, 500000)
        }

        mock_macro_indicators = {
            "inflation_rate": round(random.uniform(1.0, 8.5), 2),
            "interest_rate": round(random.uniform(0.25, 5.5), 2),
            "gdp_growth": round(random.uniform(-2.0, 4.5), 2)
        }

        dependencies = {
            "market_portfolio_collector_agent": None,
            "market_anomaly_detector": None,
            "db_storage": None
        }

        start_result = start_new(dependencies)
        self.assertIsNone(start_result)

        evaluation_result = evaluate_macro_factors(
            portfolio_id=random_portfolio_id,
            portfolio_data=mock_portfolio_data,
            macro_indicators=mock_macro_indicators
        )

        self.assertIsInstance(evaluation_result, dict)
        self.assertEqual(evaluation_result.get("portfolio_id"), random_portfolio_id)
        self.assertIn("impact_score", evaluation_result)
        self.assertEqual(evaluation_result.get("portfolio_data"), mock_portfolio_data)
        self.assertEqual(evaluation_result.get("macro_indicators"), mock_macro_indicators)

if __name__ == "__main__":
    unittest.main()