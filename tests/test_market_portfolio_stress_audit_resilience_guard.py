import unittest
import os
import json
import uuid
from unittest.mock import patch, MagicMock

from skills.market_portfolio_stress_audit_resilience_guard import (
    MarketPortfolioStressAuditResilienceGuard,
    market_portfolio_stress_audit_resilience_guard,
    ResilienceGuardExecutionError,
    StorageUnreachableError
)


class TestMarketPortfolioStressAuditResilienceGuard(unittest.TestCase):

    def setUp(self):
        self.test_storage = f"test_guard_{uuid.uuid4().hex[:8]}.db"
        self.guard = MarketPortfolioStressAuditResilienceGuard(storage_file=self.test_storage)

    def tearDown(self):
        if os.path.exists(self.test_storage):
            try:
                os.remove(self.test_storage)
            except OSError:
                pass

    def test_init_default_subsystems(self):
        guard = MarketPortfolioStressAuditResilienceGuard()
        self.assertTrue(len(guard.subsystems) > 0)
        self.assertIn("stress_scenario_pipeline", guard.subsystems)

    def test_audit_integrity_and_validate_healthy(self):
        res = self.guard.audit_integrity_and_validate(portfolio_id="test_p1")
        self.assertEqual(res["portfolio_id"], "test_p1")
        self.assertEqual(res["guard_status"], "HEALTHY")
        self.assertTrue(res["integrity_validated"])
        self.assertEqual(len(res["anomalies_detected"]), 0)

    def test_audit_integrity_and_validate_unhealthy_recovery(self):
        payload = {
            "portfolio_id": "test_p2",
            "status": "UNHEALTHY",
            "failing_subsystems": ["stress_scenario_pipeline"]
        }
        res = self.guard.audit_integrity_and_validate(payload)
        self.assertEqual(res["portfolio_id"], "test_p2")
        self.assertEqual(res["guard_status"], "RECOVERED")
        self.assertTrue(res["integrity_validated"])
        self.assertGreater(len(res["anomalies_detected"]), 0)
        self.assertGreater(len(res["actions_taken"]), 0)

    def test_top_level_entry_point(self):
        res = market_portfolio_stress_audit_resilience_guard(portfolio_id="top_level_test")
        self.assertIn("guard_status", res)
        self.assertIn("audit_id", res)
        self.assertEqual(res["portfolio_id"], "top_level_test")

    def test_health_check(self):
        res = self.guard.health_check()
        self.assertEqual(res["status"], "HEALTHY")
        self.assertEqual(res["resilience_guard"], "OPERATIONAL")


if __name__ == '__main__':
    unittest.main()
