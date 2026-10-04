import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import io
import json
import sys

from skills.market_portfolio_stress_resilience_synthesizer import (
    MarketPortfolioStressResilienceSynthesizer,
    market_portfolio_stress_resilience_synthesizer
)


class TestMarketPortfolioStressResilienceSynthesizer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.db_storage = MagicMock()
        self.monte_carlo_engine = MagicMock()
        self.scenario_simulator = MagicMock()
        self.recovery_coordinator = MagicMock()

        self.synthesizer = MarketPortfolioStressResilienceSynthesizer(
            db_storage=self.db_storage,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_engine,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_stress_recovery_coordinator_bridge=self.recovery_coordinator
        )

    def test_validate_portfolio_id_valid(self):
        valid_id = str(uuid.uuid4())
        try:
            self.synthesizer._validate_portfolio_id(valid_id)
        except Exception as e:
            self.fail(f"_validate_portfolio_id raised unexpected exception: {e}")

    def test_validate_portfolio_id_invalid(self):
        invalid_id = f"not-a-uuid-{random.randint(1000, 9999)}"
        with self.assertRaises(ValueError):
            self.synthesizer._validate_portfolio_id(invalid_id)

    def test_synthesize_success_flow(self):
        var_val = round(random.uniform(50.0, 500.0), 2)
        drawdown_val = round(random.uniform(0.05, 0.8), 2)
        recovery_days_val = random.randint(5, 120)

        self.monte_carlo_engine.calculate_var.return_value = {"var_95": var_val}
        self.scenario_simulator.run_simulation.return_value = {"max_drawdown": drawdown_val, "impact": 0.4}
        self.recovery_coordinator.estimate_recovery_time.return_value = {"recovery_days": recovery_days_val}

        result = self.synthesizer.synthesize(self.portfolio_id)

        self.assertIn("resilience_index", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("components", result)
        self.assertEqual(result["components"]["var"], var_val)
        self.assertEqual(result["components"]["max_drawdown"], drawdown_val)
        self.assertEqual(result["components"]["recovery_days"], recovery_days_val)

        expected_score = max(0.0, min(100.0, 100.0 - (float(drawdown_val) * 50.0 + float(recovery_days_val) / 5.0)))
        self.assertEqual(result["resilience_index"], expected_score)
        self.db_storage.save.assert_called_once_with(self.portfolio_id, result)

    def test_synthesize_handles_engine_exceptions_gracefully(self):
        random_err_msg = str(uuid.uuid4())
        self.monte_carlo_engine.calculate_var.side_effect = Exception(random_err_msg)

        # Mock sys.stderr.buffer to avoid TypeError when writing str to bytes buffer
        mock_stderr = MagicMock()
        with patch("sys.stderr", mock_stderr):
            result = self.synthesizer.synthesize(self.portfolio_id)

        self.assertIn("error", result)
        self.assertEqual(result["error"], random_err_msg)
        self.assertEqual(result["resilience_index"], 0.0)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)

    def test_export_report_without_exporter(self):
        with patch("skills.market_portfolio_stress_resilience_synthesizer.market_portfolio_data_exporter", None):
            res = self.synthesizer.export_report(self.portfolio_id, "some_target")
            self.assertEqual(res, f"report_{self.portfolio_id}")

    def test_export_report_with_exporter(self):
        mock_exporter = MagicMock()
        expected_output = str(uuid.uuid4())
        mock_exporter.generate_report.return_value = expected_output

        with patch("skills.market_portfolio_stress_resilience_synthesizer.market_portfolio_data_exporter", mock_exporter):
            res = self.synthesizer.export_report(self.portfolio_id, "target_obj")
            self.assertEqual(res, expected_output)
            mock_exporter.generate_report.assert_called_once_with(self.portfolio_id, "target_obj")

    def test_functional_helper_wrapper(self):
        sub_portfolio_id = str(uuid.uuid4())
        sub_run_id = str(uuid.uuid4())
        sub_db_path = f"sqlite:///test_dir_{uuid.uuid4().hex}/test_market.db"

        payload = {
            "portfolio_id": sub_portfolio_id,
            "simulation_run_id": sub_run_id,
            "db_storage": sub_db_path
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            with patch("os.makedirs") as mock_makedirs:
                res = market_portfolio_stress_resilience_synthesizer(payload)

                self.assertEqual(res["portfolio_id"], sub_portfolio_id)
                self.assertEqual(res["simulation_run_id"], sub_run_id)
                self.assertIn("aggregate_resilience_score", res)
                self.assertIn("artifact_path", res)
                mock_file.assert_called_once()
                mock_makedirs.assert_called_once()


if __name__ == "__main__":
    unittest.main()