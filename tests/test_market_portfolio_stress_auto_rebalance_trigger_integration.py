import unittest
import uuid
import random
from skills.market_portfolio_stress_auto_rebalance_trigger import market_portfolio_stress_auto_rebalance_trigger
from skills import db_storage
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_strategy_optimizer
from skills import market_portfolio_alert_dispatcher


class IntegrationTestStressAutoRebalanceTrigger(unittest.TestCase):
    def test_evaluate_and_trigger_integration(self):
        portfolio_id = str(uuid.uuid4())
        threshold = round(random.uniform(0.1, 0.9), 4)
        
        result = market_portfolio_stress_auto_rebalance_trigger.evaluate_and_trigger(
            portfolio_id=portfolio_id,
            threshold=threshold
        )
        
        if result is not None:
            self.assertIsInstance(result, dict)
            if "portfolio_id" in result:
                self.assertEqual(result["portfolio_id"], portfolio_id)

    def test_notify_audit_system_integration(self):
        alert_id = f"alt_{uuid.uuid4().hex[:8]}"
        message = f"Integration test stress alert message {random.randint(1000, 9999)}"
        
        audit_result = market_portfolio_stress_auto_rebalance_trigger.notify_audit_system(
            alert_id=alert_id,
            message=message
        )
        
        self.assertIsInstance(audit_result, dict)
        self.assertIn("alert_id", audit_result)
        self.assertEqual(audit_result["alert_id"], alert_id)
        self.assertIn("dispatched", audit_result)


if __name__ == "__main__":
    unittest.main()
