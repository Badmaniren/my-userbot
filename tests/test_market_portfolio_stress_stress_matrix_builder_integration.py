import unittest
import uuid
import os
import random
from skills.market_portfolio_stress_stress_matrix_builder import market_portfolio_stress_stress_matrix_builder, start_new

class TestMarketPortfolioStressStressMatrixBuilderIntegration(unittest.TestCase):
    def test_stress_matrix_builder_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        liquidity_shock_factor = round(random.uniform(0.01, 0.5), 4)
        output_target = f"test_stress_matrix_{uuid.uuid4().hex[:8]}.json"

        builder_input = {
            "portfolio_id": portfolio_id,
            "liquidity_shock_factor": liquidity_shock_factor,
            "output_target": output_target
        }

        try:
            result = market_portfolio_stress_stress_matrix_builder(builder_input)

            self.assertIn("matrix_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["output_path"], output_target)

            self.assertTrue(os.path.exists(output_target), "Файл стресс-матрицы не был создан на диске.")
            
            with open(output_target, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(portfolio_id, content)
                self.assertIn(result["matrix_id"], content)

            start_result = start_new(
                portfolio_id=portfolio_id,
                liquidity_shock_factor=liquidity_shock_factor
            )
            self.assertIn("matrix_id", start_result)
            self.assertEqual(start_result["portfolio_id"], portfolio_id)

        finally:
            if os.path.exists(output_target):
                try:
                    os.remove(output_target)
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()