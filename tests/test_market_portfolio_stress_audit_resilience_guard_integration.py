import unittest
import uuid
from skills.market_portfolio_stress_audit_resilience_guard import (
    MarketPortfolioStressAuditResilienceGuard,
    market_portfolio_stress_audit_resilience_guard
)
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_report_generator import market_report_generator
from skills.db_storage import db_storage

class TestMarketPortfolioStressAuditResilienceGuardIntegration(unittest.TestCase):
    def test_audit_integrity_and_validate_flow(self):
        scenario_id = f"scenario-{uuid.uuid4()}"
        portfolio_id = f"port-{uuid.uuid4()}"
        random_payload = uuid.uuid4().bytes + uuid.uuid4().bytes

        guard_instance = MarketPortfolioStressAuditResilienceGuard(
            db_storage=db_storage,
            market_report_generator=market_report_generator,
            market_portfolio_stress_scenario_pipeline=market_portfolio_stress_scenario_pipeline
        )

        audit_result = guard_instance.audit_integrity_and_validate(
            report_payload=random_payload,
            scenario_id=scenario_id
        )

        self.assertEqual(audit_result["status"], "SECURE_INTEGRITY_VERIFIED")
        self.assertEqual(audit_result["scenario_id"], scenario_id)
        self.assertEqual(audit_result["bytes_audited"], len(random_payload))
        self.assertIn("validation_token", audit_result)
        self.assertTrue(len(audit_result["validation_token"]) > 0)

        guard_input = {
            "expected_portfolio_id": portfolio_id,
            "audit_report": {
                "scenario_data": {
                    "portfolio_id": portfolio_id
                }
            }
        }

        resilience_result = market_portfolio_stress_audit_resilience_guard(guard_input)

        self.assertTrue(resilience_result["is_resilient"])
        self.assertEqual(resilience_result["verified_portfolio_id"], portfolio_id)
        self.assertEqual(resilience_result["audit_score"], 1.0)

    def test_invalid_payload_raises_error(self):
        guard_instance = MarketPortfolioStressAuditResilienceGuard()
        scenario_id = str(uuid.uuid4())

        with self.assertRaises(ValueError):
            guard_instance.audit_integrity_and_validate(
                report_payload=b"",
                scenario_id=scenario_id
            )

    def test_missing_scenario_id_raises_error(self):
        guard_instance = MarketPortfolioStressAuditResilienceGuard()
        payload = uuid.uuid4().bytes

        with self.assertRaises(ValueError):
            guard_instance.audit_integrity_and_validate(
                report_payload=payload,
                scenario_id=""
            )

if __name__ == "__main__":
    unittest.main()