import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_deep_diagnostics import (
    market_portfolio_stress_audit_deep_diagnostics,
    market_portfolio_scenario_simulator,
    market_portfolio_stress_scenario_matrix_evaluator,
    market_portfolio_stress_ml_volatility_forecaster_v2,
    db_storage
)

class TestMarketPortfolioStressAuditDeepDiagnosticsIntegration(unittest.TestCase):
    def test_deep_diagnostics_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_seed = random.randint(1000, 99999)
        stress_factor = round(random.uniform(1.0, 5.0), 2)

        sim_result = market_portfolio_scenario_simulator(
            portfolio_id=portfolio_id,
            seed=simulation_seed,
            factor=stress_factor
        )
        self.assertIsNotNone(sim_result)

        matrix_eval = market_portfolio_stress_scenario_matrix_evaluator(
            simulation_data=sim_result,
            threshold=stress_factor
        )
        self.assertIsNotNone(matrix_eval)

        vol_forecast = market_portfolio_stress_ml_volatility_forecaster_v2(
            evaluation_matrix=matrix_eval,
            confidence_level=0.95
        )
        self.assertIsNotNone(vol_forecast)

        diagnostic_report = market_portfolio_stress_audit_deep_diagnostics(
            portfolio_id=portfolio_id,
            volatility_data=vol_forecast
        )
        self.assertIn("root_cause", diagnostic_report)

        storage_status = db_storage(
            record_id=portfolio_id,
            payload=diagnostic_report
        )
        self.assertTrue(storage_status)

if __name__ == "__main__":
    unittest.main()