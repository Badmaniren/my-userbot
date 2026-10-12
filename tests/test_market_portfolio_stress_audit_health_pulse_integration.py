import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_health_pulse import (
    db_storage,
    market_portfolio_stress_scenario_pipeline,
    market_report_generator
)

class TestMarketPortfolioStressAuditHealthPulseIntegration(unittest.TestCase):

    def test_health_pulse_and_stress_pipeline_integration(self):
        unique_run_id = f"audit_run_{uuid.uuid4().hex[:8]}"
        portfolio_id = f"port_{random.randint(1000, 9999)}"
        test_db_key = f"health_pulse_state_{uuid.uuid4().hex}"

        db_storage_instance = db_storage()
        pipeline_instance = market_portfolio_stress_scenario_pipeline()
        report_generator_instance = market_report_generator()

        health_check_result = db_storage_instance.health_pulse(
            run_id=unique_run_id,
            target_portfolio=portfolio_id,
            state_key=test_db_key
        )

        self.assertIsNotNone(health_check_result)
        self.assertIn("status", health_check_result)

        pipeline_payload = {
            "run_id": unique_run_id,
            "portfolio_id": portfolio_id,
            "pulse_status": health_check_result["status"],
            "stress_factor": random.uniform(0.01, 0.99)
        }

        pipeline_execution = pipeline_instance.execute_stress_scenario(pipeline_payload)
        self.assertIsNotNone(pipeline_execution)
        self.assertEqual(pipeline_execution.get("run_id"), unique_run_id)

        report_output = report_generator_instance.generate_audit_report(
            run_id=unique_run_id,
            metrics=pipeline_execution
        )

        self.assertIsNotNone(report_output)

        if isinstance(report_output, dict) and "file_path" in report_output:
            file_path = report_output["file_path"]
            self.assertTrue(os.path.exists(file_path))
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    unittest.main()