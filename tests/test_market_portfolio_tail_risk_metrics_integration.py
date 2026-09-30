import unittest
import uuid
import random
import os
from datetime import datetime

from skills.market_portfolio_tail_risk_metrics import calculate_tail_risk_metrics
from skills.market_portfolio_scenario_simulator import run_scenario_simulation
from skills.db_storage import save_portfolio_state, get_portfolio_state


class TestMarketPortfolioTailRiskMetricsIntegration(unittest.TestCase):

    def test_tail_risk_metrics_real_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)

        portfolio_data = {
            "portfolio_id": portfolio_id,
            "capital": initial_capital,
            "assets": {
                "AAPL": round(random.uniform(0.1, 0.5), 2),
                "MSFT": round(random.uniform(0.1, 0.5), 2),
                "GOOGL": round(random.uniform(0.1, 0.4), 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        save_res = save_portfolio_state(portfolio_data)
        self.assertIsNotNone(save_res)

        sim_result = run_scenario_simulation(
            portfolio_id=portfolio_id,
            runs=simulation_runs,
            horizon_days=30
        )
        self.assertIn("simulation_id", sim_result)
        simulation_id = sim_result["simulation_id"]

        risk_metrics = calculate_tail_risk_metrics(
            portfolio_id=portfolio_id,
            simulation_id=simulation_id,
            confidence=confidence_level
        )

        self.assertIsInstance(risk_metrics, dict)
        self.assertIn("expected_shortfall", risk_metrics)
        self.assertIn("conditional_var", risk_metrics)
        self.assertEqual(risk_metrics.get("portfolio_id"), portfolio_id)
        self.assertGreater(risk_metrics["expected_shortfall"], 0.0)
        self.assertGreater(risk_metrics["conditional_var"], 0.0)

        stored_state = get_portfolio_state(portfolio_id)
        self.assertEqual(stored_state["portfolio_id"], portfolio_id)
        self.assertIn("tail_risk_metrics", stored_state.get("metadata", {}))


if __name__ == "__main__":
    unittest.main()