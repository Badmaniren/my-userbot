import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_var_calibrator import market_portfolio_stress_var_calibrator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage

class TestMarketPortfolioStressVarCalibratorIntegration(unittest.TestCase):
    def test_var_calibrator_integration(self):
        portfolio_id = str(uuid.uuid4())
        sim_run_id = f"sim_{uuid.uuid4().hex[:8]}"
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        num_simulations = random.randint(1000, 50000)

        mc_engine = market_portfolio_stress_monte_carlo_engine()
        sim_result = mc_engine.run_simulation(
            portfolio_id=portfolio_id,
            run_id=sim_run_id,
            iterations=num_simulations
        )

        self.assertIsNotNone(sim_result)

        calibrator = market_portfolio_stress_var_calibrator()
        calibration_result = calibrator.calibrate_var(
            portfolio_id=portfolio_id,
            simulation_data=sim_result,
            confidence=confidence_level
        )

        self.assertIn("var_value", calibration_result)
        self.assertIn("expected_shortfall", calibration_result)
        self.assertEqual(calibration_result.get("portfolio_id"), portfolio_id)

        storage = db_storage()
        stored_record = storage.get_var_calibration(portfolio_id)
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("confidence"), confidence_level)

if __name__ == "__main__":
    unittest.main()