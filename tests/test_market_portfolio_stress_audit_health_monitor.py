import unittest
import uuid
import random
import time
from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    market_portfolio_stress_audit_health_monitor,
)
from skills.market_portfolio_stress_audit_summary_vault import (
    MarketPortfolioStressAuditSummaryVault,
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):
    def setUp(self):
        self.health_monitor = market_portfolio_stress_audit_health_monitor()
        self.summary_vault = MarketPortfolioStressAuditSummaryVault()

    def test_check_audit_integrity_found_and_health_levels(self):
        audit_id_critical = f"AUDIT-CRITICAL-{uuid.uuid4()}"
        self.summary_vault.save_audit_summary(
            audit_id_critical,
            {
                "audit_id": audit_id_critical,
                "risk_index": 0.85,
                "timestamp": time.time(),
                "integrity_hash": "hash_crit",
            },
        )

        res_crit = self.health_monitor.check_audit_integrity(audit_id_critical)
        self.assertEqual(res_crit["status"], "OK")
        self.assertTrue(res_crit["is_healthy"])
        self.assertEqual(res_crit["health_level"], "CRITICAL")
        self.assertEqual(res_crit["observed_risk"], 0.85)

        audit_id_warn = f"AUDIT-WARN-{uuid.uuid4()}"
        self.summary_vault.save_audit_summary(
            audit_id_warn,
            {
                "audit_id": audit_id_warn,
                "risk_index": 0.65,
            },
        )
        res_warn = self.health_monitor.check_audit_integrity(audit_id_warn)
        self.assertEqual(res_warn["health_level"], "WARNING")

        audit_id_stable = f"AUDIT-STABLE-{uuid.uuid4()}"
        self.summary_vault.save_audit_summary(
            audit_id_stable,
            {
                "audit_id": audit_id_stable,
                "risk_index": 0.2,
            },
        )
        res_stable = self.health_monitor.check_audit_integrity(audit_id_stable)
        self.assertEqual(res_stable["health_level"], "STABLE")

    def test_check_audit_integrity_not_found(self):
        non_existent_id = f"NO-AUDIT-{uuid.uuid4()}"
        res = self.health_monitor.check_audit_integrity(non_existent_id)
        self.assertEqual(res["status"], "NOT_FOUND")
        self.assertFalse(res["is_healthy"])
        self.assertEqual(res["health_level"], "UNKNOWN")

    def test_generate_aggregate_health_report(self):
        audit_ids = [f"AGG-{uuid.uuid4()}" for _ in range(3)]
        for idx, aid in enumerate(audit_ids):
            self.summary_vault.save_audit_summary(
                aid,
                {"audit_id": aid, "risk_index": 0.1 * (idx + 1)},
            )

        report = self.health_monitor.generate_aggregate_health_report(audit_ids)
        self.assertEqual(report["total_count"], 3)
        self.assertEqual(report["processed_items"], audit_ids)
        self.assertEqual(len(report["report_map"]), 3)
        for aid in audit_ids:
            self.assertIn(aid, report["report_map"])
            self.assertTrue(report["report_map"][aid]["is_healthy"])


if __name__ == "__main__":
    unittest.main()
