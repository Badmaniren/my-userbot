import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_compliance_validator import validate_portfolio_stress_compliance
from skills.db_storage import save_audit_record, get_audit_record
from skills.market_portfolio_stress_reporter import generate_stress_report
from skills.market_portfolio_scenario_simulator import simulate_scenario

class TestMarketPortfolioStressComplianceValidatorIntegration(unittest.TestCase):

    def test_stress_compliance_validator_end_to_end(self):
        unique_portfolio_id = f"port-{uuid.uuid4()}"
        unique_audit_id = f"audit-{uuid.uuid4()}"
        random_shock_factor = round(random.uniform(0.05, 0.35), 4)
        random_liquidity_threshold = random.randint(100000, 5000000)

        simulation_result = simulate_scenario(
            portfolio_id=unique_portfolio_id,
            shock_factor=random_shock_factor,
            threshold=random_liquidity_threshold
        )
        self.assertIsNotNone(simulation_result, "Simulation result must not be None")

        report_payload = {
            "audit_id": unique_audit_id,
            "portfolio_id": unique_portfolio_id,
            "simulation_data": simulation_result,
            "compliance_status": "PENDING"
        }
        report_id = generate_stress_report(report_payload)
        self.assertIsNotNone(report_id, "Stress report must generate an ID")

        storage_saved = save_audit_record(unique_audit_id, {
            "portfolio_id": unique_portfolio_id,
            "report_id": report_id,
            "shock_factor": random_shock_factor,
            "threshold": random_liquidity_threshold
        })
        self.assertTrue(storage_saved, "Audit record must be successfully stored in db_storage")

        stored_record = get_audit_record(unique_audit_id)
        self.assertEqual(stored_record["portfolio_id"], unique_portfolio_id)

        validation_result = validate_portfolio_stress_compliance(unique_audit_id)

        self.assertIsInstance(validation_result, dict, "Validation result must be a dictionary")
        self.assertIn("is_compliant", validation_result, "Validation result must contain compliance status")
        self.assertEqual(validation_result.get("audit_id"), unique_audit_id, "Validation must process the exact target audit ID")

        output_artifact_path = f"compliance_report_{unique_audit_id}.log"
        self.assertTrue(os.path.exists(output_artifact_path), "Validator must produce a real compliance execution artifact on disk")

        if os.path.exists(output_artifact_path):
            os.remove(output_artifact_path)

if __name__ == "__main__":
    unittest.main()