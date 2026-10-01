import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_audit_logger import (
    market_portfolio_stress_audit_logger,
    db_storage,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_stress_monte_carlo_engine
)

class TestMarketPortfolioStressAuditLoggerIntegration(unittest.TestCase):
    def test_stress_audit_logger_end_to_end_flow(self):
        portfolio_id = str(uuid.uuid4())
        scenario_id = str(uuid.uuid4())

        market_shock_factor = round(random.uniform(0.05, 0.45), 4)
        confidence_level = random.choice([0.95, 0.99])
        monte_carlo_iterations = random.randint(1000, 5000)

        scenario_data = {
            "scenario_id": scenario_id,
            "portfolio_id": portfolio_id,
            "shock_factor": market_shock_factor,
            "confidence": confidence_level
        }

        pipeline_result = market_portfolio_stress_scenario_pipeline(scenario_data)

        mc_config = {
            "scenario_id": scenario_id,
            "iterations": monte_carlo_iterations,
            "pipeline_context": pipeline_result
        }
        mc_simulation_output = market_portfolio_stress_monte_carlo_engine(mc_config)

        audit_payload = {
            "audit_id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "simulation_results": mc_simulation_output,
            "status": "COMPLETED"
        }

        logger_response = market_portfolio_stress_audit_logger(audit_payload)

        self.assertIsNotNone(logger_response)
        self.assertIn("logged_id", logger_response)
        self.assertEqual(logger_response["portfolio_id"], portfolio_id)

        db_record = db_storage(f"get_audit_{portfolio_id}")
        self.assertIsNotNone(db_record)
        self.assertEqual(db_record.get("scenario_id"), scenario_id)

if __name__ == "__main__":
    unittest.main()