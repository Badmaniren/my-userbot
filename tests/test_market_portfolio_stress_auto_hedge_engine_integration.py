import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_engine import (
    market_portfolio_stress_auto_hedge_engine,
    db_storage,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_stress_monte_carlo_engine,
    market_portfolio_stress_auto_rebalance_trigger,
    market_portfolio_execution_pipeline
)

class TestMarketPortfolioStressAutoHedgeEngineIntegration(unittest.TestCase):
    def test_end_to_end_stress_auto_hedge_workflow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        scenario_id = f"scen-{uuid.uuid4()}"
        initial_balance = round(random.uniform(10000.0, 1000000.0), 2)
        risk_tolerance = round(random.uniform(0.01, 0.25), 4)

        db_storage(
            action="init_portfolio",
            portfolio_id=portfolio_id,
            balance=initial_balance,
            risk_tolerance=risk_tolerance
        )

        scenario_result = market_portfolio_stress_scenario_pipeline(
            scenario_id=scenario_id,
            portfolio_id=portfolio_id,
            severity_index=round(random.uniform(1.0, 10.0), 2)
        )
        self.assertIn("scenario_id", scenario_result)

        mc_evaluation = market_portfolio_stress_monte_carlo_engine(
            scenario_id=scenario_id,
            iterations=random.randint(100, 1000)
        )
        self.assertIn("var_95", mc_evaluation)

        rebalance_signal = market_portfolio_stress_auto_rebalance_trigger(
            portfolio_id=portfolio_id,
            monte_carlo_metrics=mc_evaluation
        )
        self.assertTrue(rebalance_signal.get("triggered", True))

        execution_result = market_portfolio_execution_pipeline(
            portfolio_id=portfolio_id,
            action_payload=rebalance_signal
        )
        self.assertIn("execution_id", execution_result)

        hedge_result = market_portfolio_stress_auto_hedge_engine(
            portfolio_id=portfolio_id,
            execution_id=execution_result["execution_id"],
            hedge_factor=risk_tolerance
        )

        self.assertEqual(hedge_result.get("portfolio_id"), portfolio_id)
        self.assertIn("status", hedge_result)
        self.assertEqual(hedge_result["status"], "success")

        state_check = db_storage(action="get_portfolio", portfolio_id=portfolio_id)
        self.assertIsNotNone(state_check)

if __name__ == "__main__":
    unittest.main()