import unittest
import uuid
import random
from skills.market_portfolio_stress_auto_rebalance_trigger import market_portfolio_stress_auto_rebalance_trigger
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator

class TestIntegrationStressAutoRebalanceTrigger(unittest.TestCase):
    def test_evaluate_and_trigger_integration(self):
        unique_portfolio_id = f"port_{uuid.uuid4().hex}"
        dynamic_threshold = round(random.uniform(0.1, 0.9), 4)

        if hasattr(market_portfolio_scenario_simulator, "run_simulation"):
            market_portfolio_scenario_simulator.run_simulation(
                portfolio_id=unique_portfolio_id,
                threshold=dynamic_threshold
            )

        result = market_portfolio_stress_auto_rebalance_trigger.evaluate_and_trigger(
            portfolio_id=unique_portfolio_id,
            threshold=dynamic_threshold
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        
        signal_id = result.get("rebalance_signal_id")
        self.assertIsNotNone(signal_id)

        if db_storage and hasattr(db_storage, "load"):
            stored_data = db_storage.load(signal_id)
            if stored_data:
                self.assertEqual(stored_data.get("portfolio_id"), unique_portfolio_id)
                self.assertEqual(stored_data.get("status"), "TRIGGERED")

    def test_execute_rebalance_integration(self):
        unique_portfolio_id = f"port_{uuid.uuid4().hex}"
        hedges = [{"asset": "USDT", "amount": 5000}]
        weights = {"BTC": 0.4, "ETH": 0.4, "USDT": 0.2}

        result = market_portfolio_stress_auto_rebalance_trigger.execute_rebalance(
            portfolio_id=unique_portfolio_id,
            hedges=hedges,
            weights=weights
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), unique_portfolio_id)
        self.assertEqual(result.get("status"), "EXECUTED")
        self.assertEqual(result.get("hedges"), hedges)

    def test_notify_audit_system_integration(self):
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        message = f"Stress test warning message {random.randint(1000, 9999)}"

        response = market_portfolio_stress_auto_rebalance_trigger.notify_audit_system(
            alert_id=alert_id,
            message=message
        )

        self.assertIsInstance(response, dict)
        self.assertIn("alert_id", response)
        self.assertEqual(response.get("alert_id"), alert_id)
        self.assertIn("dispatched", response)

if __name__ == "__main__":
    unittest.main()
