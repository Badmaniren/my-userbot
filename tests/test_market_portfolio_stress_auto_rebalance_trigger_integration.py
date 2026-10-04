import unittest
import uuid
import random
from skills.market_portfolio_stress_auto_rebalance_trigger import market_portfolio_stress_auto_rebalance_trigger

class IntegrationTestStressAutoRebalanceTrigger(unittest.TestCase):
    def test_evaluate_and_trigger_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:12]}"
        dynamic_threshold = round(random.uniform(0.1, 0.9), 4)
        
        result = market_portfolio_stress_auto_rebalance_trigger.evaluate_and_trigger(
            portfolio_id=portfolio_id, 
            threshold=dynamic_threshold
        )
        
        if result is not None:
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            
        alert_id = f"alt_{uuid.uuid4().hex[:8]}"
        message = f"Critical stress threshold breached for portfolio {portfolio_id} with score {random.uniform(0.5, 1.0)}"
        
        audit_res = market_portfolio_stress_auto_rebalance_trigger.notify_audit_system(
            alert_id=alert_id,
            message=message
        )
        
        self.assertIsInstance(audit_res, dict)
        self.assertIn("alert_id", audit_res)
        self.assertEqual(audit_res["alert_id"], alert_id)
        self.assertIn("dispatched", audit_res)

if __name__ == "__main__":
    unittest.main()