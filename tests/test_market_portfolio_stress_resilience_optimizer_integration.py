import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_resilience_optimizer import (
    market_portfolio_stress_resilience_optimizer
)
from skills.market_portfolio_scenario_simulator import (
    market_portfolio_scenario_simulator
)
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault
)
from skills.db_storage import db_storage

class TestMarketPortfolioStressResilienceOptimizerIntegration(unittest.TestCase):

    def test_stress_resilience_optimization_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        audit_metric_id = random.randint(1000, 99999)
        shock_level = round(random.uniform(0.05, 0.45), 4)

        audit_data = {
            "audit_metric_id": audit_metric_id,
            "health_score": round(random.uniform(50.0, 100.0), 2),
            "volatility": round(random.uniform(0.1, 0.5), 4)
        }
        vault_saved = market_portfolio_stress_audit_summary_vault(portfolio_id, audit_data)
        self.assertTrue(vault_saved, "Vault should successfully save audit health metrics.")

        simulation_params = {
            "shock_level": shock_level,
            "confidence_interval": 0.95
        }
        simulated_results = market_portfolio_scenario_simulator(portfolio_id, simulation_params)
        self.assertIn("simulation_id", simulated_results)

        optimization_payload = {
            "portfolio_id": portfolio_id,
            "audit_metric_id": audit_metric_id,
            "scenario_ref": simulated_results["simulation_id"],
            "target_resilience": round(random.uniform(0.8, 0.99), 4)
        }

        optimizer_response = market_portfolio_stress_resilience_optimizer(optimization_payload)

        self.assertIsInstance(optimizer_response, dict)
        self.assertIn("optimized_portfolio_id", optimizer_response)
        self.assertEqual(optimizer_response["optimized_portfolio_id"], portfolio_id)
        self.assertIn("resilience_score", optimizer_response)

        persisted_state = db_storage(f"get_resilience:{portfolio_id}")
        self.assertIsNotNone(persisted_state)

if __name__ == "__main__":
    unittest.main()