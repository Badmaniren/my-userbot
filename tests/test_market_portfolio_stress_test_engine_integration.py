import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_test_engine import market_portfolio_stress_test_engine
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_anomaly_detector import market_anomaly_detector

class TestMarketPortfolioStressTestEngineIntegration(unittest.TestCase):
    def test_stress_test_execution_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        shock_magnitude = round(random.uniform(-0.5, -0.1), 2)

        simulation_data = {
            "portfolio_id": portfolio_id,
            "shock_type": "black_swan",
            "magnitude": shock_magnitude,
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "value": random.randint(1000, 50000)},
                {"ticker": "TSLA", "weight": 0.5, "value": random.randint(1000, 50000)}
            ]
        }

        sim_result = market_portfolio_scenario_simulator(simulation_data)
        self.assertIsNotNone(sim_result)

        anomaly_payload = {
            "portfolio_id": portfolio_id,
            "variance_threshold": random.uniform(0.01, 0.05)
        }
        anomaly_data = market_anomaly_detector(anomaly_payload)

        stress_input = {
            "portfolio_id": portfolio_id,
            "simulation": sim_result,
            "anomaly_data": anomaly_data,
            "persist": True
        }

        stress_output = market_portfolio_stress_test_engine(stress_input)

        self.assertIsInstance(stress_output, dict)
        self.assertIn("resilience_score", stress_output)

        db_check = db_storage({"action": "get", "key": f"stress_test_{portfolio_id}"})
        self.assertIsNotNone(db_check)

if __name__ == "__main__":
    unittest.main()