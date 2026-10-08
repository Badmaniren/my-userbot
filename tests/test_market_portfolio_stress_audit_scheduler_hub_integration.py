import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_scheduler_hub import (
    market_portfolio_stress_audit_scheduler_hub_process
)
from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def test_scheduler_hub_composition_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        threshold = round(random.uniform(0.01, 0.5), 4)
        storage_target = f"test_audit_storage_{uuid.uuid4().hex[:8]}.json"
        
        audit_data = {
            "audit_id": f"audit_{uuid.uuid4().hex[:8]}",
            "portfolio_id": portfolio_id,
            "threshold": threshold,
            "status": "COMPLETED",
            "score": random.randint(1, 100)
        }

        try:
            trigger_instance = StressAutoRebalanceTrigger()
            self.assertIsNotNone(trigger_instance)

            vault_init_result = start_new()
            self.assertIsNotNone(vault_init_result)

            vault_process_result = market_portfolio_stress_audit_summary_vault_process(
                storage_target, audit_data
            )
            self.assertIsNotNone(vault_process_result)

            is_valid = market_portfolio_stress_audit_summary_vault_validate(
                storage_target, audit_data["audit_id"]
            )
            self.assertTrue(is_valid)

            exported_data = market_portfolio_stress_audit_summary_vault_export(
                storage_target, "json"
            )
            self.assertIsNotNone(exported_data)

            hub_result = market_portfolio_stress_audit_scheduler_hub_process(
                portfolio_id=portfolio_id,
                threshold=threshold,
                storage_target=storage_target,
                audit_data=audit_data
            )
            self.assertIsNotNone(hub_result)

        finally:
            if os.path.exists(storage_target):
                try:
                    os.remove(storage_target)
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()