import unittest
from unittest.mock import patch
import uuid
import random
import math
import io

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 15)
        self.initial_value = round(random.uniform(10000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_with_db_storage(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch:
            with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:
                result = self.engine.run_simulation(
                    portfolio_id=self.portfolio_id,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days
                )

                mock_fetch.assert_called_once_with(self.portfolio_id)
                mock_anomaly.assert_called_once()

                self.assertIsInstance(result, dict)
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertIn("simulation_results", result)
                self.assertIn("var_95", result)
                self.assertIn("cvar_95", result)
                self.assertEqual(len(result["simulation_results"]), self.simulations)
                for path in result["simulation_results"]:
                    self.assertEqual(len(path), self.horizon_days)

    def test_run_simulation_fallback_db_storage(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("No anomaly")):
                result = self.engine.run_simulation(
                    portfolio_id=self.portfolio_id,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days
                )

                self.assertIsInstance(result, dict)
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertIn("var_95", result)
                self.assertIn("cvar_95", result)

    def test_export_report_success(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        expected_export_result = {
            "report_id": report_id,
            "loss_limit": loss_limit,
            "status": "exported"
        }

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export_result) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_export_result)

    def test_export_report_fallback(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        random_stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=mock_stream) as mock_gateway:
            res = self.engine.consume_stream()
            mock_gateway.assert_called_once()
            self.assertEqual(res.read(), random_stream_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        iterations = random.randint(10, 40)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], self.initial_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()