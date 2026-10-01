import unittest
import uuid
import random
import os
import time

from skills.market_portfolio_var_telemetry_collector import (
    market_portfolio_var_telemetry_collector
)
from skills.market_portfolio_scenario_simulator import (
    market_portfolio_scenario_simulator
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine
)
from skills.db_storage import db_storage

class TestMarketPortfolioVarTelemetryCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.run_id = str(uuid.uuid4())
        self.simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.portfolio_value = round(random.uniform(100000.0, 10000000.0), 2)

    def test_var_telemetry_end_to_end_flow(self):
        sim_input = {
            "simulation_id": self.simulation_id,
            "run_id": self.run_id,
            "confidence": self.confidence_level,
            "initial_capital": self.portfolio_value,
            "horizon_days": random.randint(1, 30)
        }

        monte_carlo_res = market_portfolio_stress_monte_carlo_engine(sim_input)
        self.assertIsNotNone(monte_carlo_res)

        scenario_payload = {
            "simulation_id": self.simulation_id,
            "monte_carlo_data": monte_carlo_res,
            "metric_type": "VaR"
        }

        scenario_res = market_portfolio_scenario_simulator(scenario_payload)
        self.assertIn("var_result", scenario_res)

        telemetry_payload = {
            "run_id": self.run_id,
            "simulation_id": self.simulation_id,
            "scenario_output": scenario_res,
            "timestamp": time.time()
        }

        telemetry_result = market_portfolio_var_telemetry_collector(telemetry_payload)

        self.assertIsInstance(telemetry_result, dict)
        self.assertEqual(telemetry_result.get("run_id"), self.run_id)
        self.assertEqual(telemetry_result.get("simulation_id"), self.simulation_id)
        self.assertIn("telemetry_id", telemetry_result)

        telemetry_record_id = telemetry_result["telemetry_id"]
        stored_data = db_storage({"action": "get", "table": "var_telemetry", "id": telemetry_record_id})

        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data.get("run_id"), self.run_id)
        self.assertAlmostEqual(float(stored_data.get("portfolio_value", 0)), self.portfolio_value, places=2)

if __name__ == "__main__":
    unittest.main()