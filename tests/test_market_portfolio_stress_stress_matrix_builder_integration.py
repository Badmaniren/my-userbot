import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_stress_matrix_builder import (
    market_portfolio_stress_stress_matrix_builder
)
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_valuation import market_portfolio_valuation

class TestMarketPortfolioStressMatrixBuilderIntegration(unittest.TestCase):

    def test_stress_matrix_builder_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_count = random.randint(3, 10)
        shock_magnitude = round(random.uniform(-0.5, -0.1), 2)
        
        valuation_input = {
            "portfolio_id": portfolio_id,
            "assets": [
                {
                    "ticker": f"TICK_{i}",
                    "volume": random.randint(100, 5000),
                    "current_price": round(random.uniform(10.0, 1000.0), 2)
                } for i in range(asset_count)
            ]
        }
        
        valuation_result = market_portfolio_valuation(valuation_input)
        self.assertIsNotNone(valuation_result)

        simulator_input = {
            "portfolio_id": portfolio_id,
            "base_valuation": valuation_result,
            "liquidity_shock": shock_magnitude
        }
        
        simulation_data = market_portfolio_scenario_simulator(simulator_input)
        self.assertIsNotNone(simulation_data)

        builder_input = {
            "portfolio_id": portfolio_id,
            "simulation_report": simulation_data,
            "matrix_resolution": random.choice([10, 20, 50]),
            "output_target": f"stress_matrix_{uuid.uuid4().hex}.json"
        }

        matrix_result = market_portfolio_stress_stress_matrix_builder(builder_input)
        
        self.assertIn("matrix_id", matrix_result)
        self.assertEqual(matrix_result["portfolio_id"], portfolio_id)
        
        generated_file = matrix_result.get("output_path")
        if generated_file:
            self.assertTrue(os.path.exists(generated_file))
            os.remove(generated_file)

        stored_record = db_storage({
            "action": "get",
            "table": "stress_matrices",
            "matrix_id": matrix_result["matrix_id"]
        })
        
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()