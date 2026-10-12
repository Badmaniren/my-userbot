import unittest
import os
import json
import uuid

from skills.market_portfolio_stress_audit_resilience_guard import (
    MarketPortfolioStressAuditResilienceGuard,
    market_portfolio_stress_audit_resilience_guard
)


class TestMarketPortfolioStressAuditResilienceGuardIntegration(unittest.TestCase):

    def setUp(self):
        self.test_storage = f"integration_guard_{uuid.uuid4().hex[:8]}.db"

    def tearDown(self):
        if os.path.exists(self.test_storage):
            try:
                os.remove(self.test_storage)
            except OSError:
                pass

    def test_end_to_end_resilience_guard_workflow(self):
        guard = MarketPortfolioStressAuditResilienceGuard(
            subsystems=["stress_scenario_pipeline", "audit_compliance_hub"],
            storage_file=self.test_storage
        )

        res1 = guard.audit_integrity_and_validate(portfolio_id="port_int_100")
        self.assertEqual(res1["guard_status"], "HEALTHY")

        res2 = guard.audit_integrity_and_validate(
            portfolio_id="port_int_100",
            stress_scenario_pipeline_status="UNHEALTHY"
        )
        self.assertEqual(res2["guard_status"], "RECOVERED")
        self.assertTrue(os.path.exists(self.test_storage))

        with open(self.test_storage, "r") as f:
            data = json.load(f)
        self.assertIn("audit_records", data)
        self.assertEqual(len(data["audit_records"]), 2)

    def test_top_level_function_integration(self):
        res = market_portfolio_stress_audit_resilience_guard({"portfolio_id": "port_top_200", "status": "HEALTHY"})
        self.assertEqual(res["portfolio_id"], "port_top_200")
        self.assertTrue(res["integrity_validated"])


if __name__ == '__main__':
    unittest.main()
