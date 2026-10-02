import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_factor_evaluator_v2 import evaluate_macro_factors
from skills.db_storage import save_macro_evaluation, get_macro_evaluation
from skills.market_portfolio_scenario_simulator import simulate_scenario

class TestMarketPortfolioMacroFactorEvaluatorV2Integration(unittest.TestCase):
    def test_macro_factor_evaluator_end_to_end(self):
        portfolio_id = str(uuid.uuid4())
        factor_name = f"inflation_rate_{random.randint(1000, 9999)}"
        factor_value = round(random.uniform(1.0, 15.0), 2)

        simulation_input = {
            "portfolio_id": portfolio_id,
            "factor": factor_name,
            "shock_value": factor_value
        }

        simulation_result = simulate_scenario(simulation_input)
        self.assertIsNotNone(simulation_result)

        evaluation_payload = {
            "portfolio_id": portfolio_id,
            "factor_name": factor_name,
            "simulated_impact": simulation_result.get("impact", factor_value * random.uniform(0.5, 2.0))
        }

        eval_result = evaluate_macro_factors(evaluation_payload)

        self.assertIn("status", eval_result)
        self.assertEqual(eval_result["status"], "success")
        self.assertEqual(eval_result["portfolio_id"], portfolio_id)

        stored_data = get_macro_evaluation(portfolio_id)
        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data.get("factor_name"), factor_name)

        report_path = f"reports/macro_eval_{portfolio_id}.json"
        self.assertTrue(os.path.exists(report_path) or eval_result.get("persisted", True))

        if os.path.exists(report_path):
            os.remove(report_path)

if __name__ == "__main__":
    unittest.main()