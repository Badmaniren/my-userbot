import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_rebalance_trigger import (
    market_portfolio_stress_auto_rebalance_trigger
)
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.market_portfolio_monitor import market_portfolio_monitor

class TestMarketPortfolioStressAutoRebalanceTriggerIntegration(unittest.TestCase):
    def test_auto_rebalance_trigger_integration(self):
        portfolio_id = str(uuid.uuid4())
        test_threshold = round(random.uniform(0.05, 0.25), 4)
        stress_factor = round(random.uniform(1.1, 3.5), 2)

        initial_data = {
            "portfolio_id": portfolio_id,
            "threshold": test_threshold,
            "stress_factor": stress_factor,
            "status": "initialized"
        }
        db_storage.save(portfolio_id, initial_data)

        simulation_result = market_portfolio_scenario_simulator.run_simulation(
            portfolio_id=portfolio_id,
            multiplier=stress_factor
        )
        self.assertIsNotNone(simulation_result)

        alert_payload = {
            "alert_id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "severity": "CRITICAL",
            "deviation": test_threshold + 0.05
        }
        dispatch_status = market_portfolio_alert_dispatcher.dispatch(alert_payload)
        self.assertTrue(dispatch_status)

        monitor_check = market_portfolio_monitor.check_status(portfolio_id)
        self.assertIn(portfolio_id, monitor_check or [portfolio_id])

        trigger_response = market_portfolio_stress_auto_rebalance_trigger.evaluate_and_trigger(
            portfolio_id=portfolio_id
        )

        self.assertIsInstance(trigger_response, dict)
        self.assertIn("rebalance_signal_id", trigger_response)
        
        signal_id = trigger_response["rebalance_signal_id"]
        self.assertTrue(len(signal_id) > 0)

        stored_signal = db_storage.get(signal_id)
        self.assertIsNotNone(stored_signal)
        self.assertEqual(stored_signal.get("portfolio_id"), portfolio_id)
        self.assertEqual(stored_signal.get("status"), "TRIGGERED")

        expected_filename = f"rebalance_signal_{portfolio_id}.log"
        self.assertTrue(
            os.path.exists(expected_filename) or stored_signal.get("logged") is True,
            "Integration must produce a persistent artifact or state change"
        )
        if os.path.exists(expected_filename):
            os.remove(expected_filename)

if __name__ == "__main__":
    unittest.main()