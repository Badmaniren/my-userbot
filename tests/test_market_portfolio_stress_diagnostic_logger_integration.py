import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_diagnostic_logger import (
    market_portfolio_stress_diagnostic_logger,
)
from skills.market_portfolio_scenario_simulator import (
    market_portfolio_scenario_simulator,
)
from skills.market_portfolio_backtester import (
    market_portfolio_backtester,
)
from skills.db_storage import (
    db_storage,
)


class TestMarketPortfolioStressDiagnosticLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
        self.backtest_id = f"bt_{uuid.uuid4().hex[:8]}"
        self.market_shock_pct = round(random.uniform(-0.35, -0.05), 4)
        self.liquidity_drain_rate = round(random.uniform(0.1, 0.9), 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stress_diagnostic_logger_end_to_end_telemetry(self):
        simulator_payload = {
            "simulation_id": self.simulation_id,
            "portfolio_id": self.portfolio_id,
            "shock_pct": self.market_shock_pct,
            "drain_rate": self.liquidity_drain_rate,
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "volatility": 0.22},
                {"ticker": "TSLA", "weight": 0.5, "volatility": 0.65}
            ]
        }

        sim_result = market_portfolio_scenario_simulator(simulator_payload)
        self.assertIsNotNone(sim_result)

        backtest_payload = {
            "backtest_id": self.backtest_id,
            "portfolio_id": self.portfolio_id,
            "initial_capital": random.randint(10000, 1000000),
            "historical_window_days": random.randint(30, 365)
        }

        bt_result = market_portfolio_backtester(backtest_payload)
        self.assertIsNotNone(bt_result)

        diagnostic_payload = {
            "diagnostic_run_id": f"diag_{uuid.uuid4().hex}",
            "portfolio_id": self.portfolio_id,
            "simulation_data": sim_result,
            "backtest_data": bt_result,
            "log_output_dir": self.temp_dir.name,
            "anomaly_threshold": round(random.uniform(1.5, 4.0), 2)
        }

        diagnostic_output = market_portfolio_stress_diagnostic_logger(diagnostic_payload)

        self.assertIsInstance(diagnostic_output, dict)
        self.assertIn("telemetry_status", diagnostic_output)
        self.assertEqual(diagnostic_output.get("portfolio_id"), self.portfolio_id)

        generated_files = os.listdir(self.temp_dir.name)
        self.assertGreater(len(generated_files), 0, "Diagnostic logger must persist telemetry logs on disk.")

        log_file_found = any(self.portfolio_id in filename or "diagnostic" in filename for filename in generated_files)
        self.assertTrue(log_file_found, "The generated log file should reflect the portfolio telemetry or diagnostic context.")

        db_payload = {
            "action": "store_diagnostic",
            "portfolio_id": self.portfolio_id,
            "diagnostic_run_id": diagnostic_output.get("diagnostic_run_id"),
            "anomaly_detected": diagnostic_output.get("anomaly_detected", False)
        }
        db_response = db_storage(db_payload)
        self.assertIsNotNone(db_response)


if __name__ == "__main__":
    unittest.main()