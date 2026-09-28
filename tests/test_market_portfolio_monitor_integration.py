import unittest
import os
import json
import tempfile
import uuid

from skills.market_portfolio_monitor import MarketPortfolioMonitor, run_pipeline, start_new
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts
from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator
)


class TestMarketPortfolioMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"integration_storage_{uuid.uuid4().hex}.json")
        self.symbol = "BTCUSD"
        self.url = "http://localhost:8000/api/portfolio"
        self.telegram_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        self.chat_id = "987654321"

        # Populate sample portfolio data structured for both monitor and scenario simulator
        initial_data = {
            self.symbol: {
                "symbol": self.symbol,
                "price": 50000.0,
                "quantity": 10.0,
                "prices": [50000.0, 60000.0, 45000.0]
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_pipeline_execution(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertEqual(result["status"], "monitored")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertAlmostEqual(result["peak"], 60000.0)
        self.assertAlmostEqual(result["trough"], 45000.0)
        self.assertAlmostEqual(result["max_drawdown"], 0.25)
        self.assertTrue(result["risk_limit_exceeded"])  # 25% > 20% default limit

    def test_alert_dispatcher_integration_with_monitor(self):
        dispatch_res = dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="HIGH",
            min_threshold="LOW"
        )

        self.assertEqual(dispatch_res["status"], "dispatched")
        self.assertIn("summary", dispatch_res)
        self.assertIn("pnl", dispatch_res)

    def test_stress_recovery_coordinator_bridge_integration(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        recovery_res = bridge.execute_recovery_workflow(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=-10.0,
            shifts=[1, 2]
        )

        self.assertIn("stress_result", recovery_res)
        self.assertIn("recovery_result", recovery_res)
        self.assertEqual(recovery_res["recovery_result"]["status"], "monitored")

        coord_output = run_stress_recovery_coordinator(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=-5.0,
            shifts=3
        )

        self.assertIn("stress", coord_output)
        self.assertIn("recovery", coord_output)
        self.assertEqual(coord_output["recovery"]["status"], "monitored")


if __name__ == "__main__":
    unittest.main()
