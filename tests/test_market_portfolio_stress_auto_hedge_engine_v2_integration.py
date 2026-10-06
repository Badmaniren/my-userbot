import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_engine_v2 import (
    market_portfolio_stress_auto_hedge_engine_v2,
    db_storage,
    market_portfolio_scenario_simulator,
    market_portfolio_execution_pipeline
)

class TestMarketPortfolioStressAutoHedgeEngineV2Integration(unittest.TestCase):
    def test_auto_hedge_engine_end_to_end_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        risk_threshold = round(random.uniform(0.05, 0.25), 4)
        capital_allocation = round(random.uniform(10000.0, 1000000.0), 2)

        simulation_data = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "risk_threshold": risk_threshold,
            "capital": capital_allocation,
            "stress_factor": random.choice([1.5, 2.0, 2.5, 3.0])
        }

        simulated_scenario = market_portfolio_scenario_simulator(simulation_data)
        self.assertIsNotNone(simulated_scenario)

        hedge_result = market_portfolio_stress_auto_hedge_engine_v2({
            "portfolio_id": portfolio_id,
            "scenario_result": simulated_scenario,
            "capital": capital_allocation
        })

        self.assertIsInstance(hedge_result, dict)
        self.assertIn("hedge_execution_id", hedge_result)

        execution_id = hedge_result["hedge_execution_id"]
        self.assertTrue(len(execution_id) > 0)

        execution_pipeline_res = market_portfolio_execution_pipeline({
            "execution_id": execution_id,
            "portfolio_id": portfolio_id,
            "actions": hedge_result.get("actions", [])
        })
        self.assertTrue(execution_pipeline_res)

        stored_record = db_storage({
            "action": "get",
            "table": "hedge_executions",
            "id": execution_id
        })
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)
        self.assertEqual(stored_record.get("status"), "executed")

if __name__ == "__main__":
    unittest.main()