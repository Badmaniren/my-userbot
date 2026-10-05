import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_scenario_matrix_evaluator import evaluate_stress_scenario_matrix
from skills.market_portfolio_scenario_simulator import simulate_market_scenarios
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation
from skills.db_storage import save_evaluation_record, get_evaluation_record

class IntegrationTestMarketPortfolioStressScenarioMatrixEvaluator(unittest.TestCase):
    def test_stress_scenario_matrix_evaluation_integration(self):
        test_portfolio_id = str(uuid.uuid4())
        test_volatility_factor = round(random.uniform(1.0, 3.5), 4)
        test_confidence_level = random.choice([0.95, 0.99])
        
        simulated_scenario = simulate_market_scenarios({
            "portfolio_id": test_portfolio_id,
            "shock_multiplier": test_volatility_factor
        })
        
        monte_carlo_result = run_monte_carlo_simulation({
            "scenario_data": simulated_scenario,
            "confidence": test_confidence_level
        })
        
        evaluation_payload = {
            "evaluation_id": str(uuid.uuid4()),
            "portfolio_id": test_portfolio_id,
            "monte_carlo_metrics": monte_carlo_result,
            "historical_weight": random.randint(100, 1000)
        }
        
        evaluation_result = evaluate_stress_scenario_matrix(evaluation_payload)
        
        self.assertIn("matrix_score", evaluation_result)
        self.assertEqual(evaluation_result["portfolio_id"], test_portfolio_id)
        
        save_evaluation_record(evaluation_result)
        persisted_record = get_evaluation_record(evaluation_payload["evaluation_id"])
        
        self.assertIsNotNone(persisted_record)
        self.assertEqual(persisted_record["evaluation_id"], evaluation_payload["evaluation_id"])
        self.assertEqual(persisted_record["matrix_score"], evaluation_result["matrix_score"])

if __name__ == "__main__":
    unittest.main()