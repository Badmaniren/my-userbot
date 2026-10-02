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
        self.simulations = random.randint(50, 150)
        self.horizon_days = random.randint(5, 30)
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_structure_and_types(self):
        portfolio_payload = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_payload):
            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)
        self.assertIsInstance(result["simulation_results"], list)
        self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_fallback_db_storage(self):
        non_existent_id = f"missing_{uuid.uuid4().hex[:6]}"
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch")):
            with patch("skills.db_storage._in_memory_db", {non_existent_id: {"portfolio_id": non_existent_id, "initial_value": self.initial_value}}):
                result = self.engine.run_simulation(
                    portfolio_id=non_existent_id,
                    simulations=10,
                    horizon_days=5
                )

        self.assertEqual(result["portfolio_id"], non_existent_id)
        self.assertGreaterEqual(result["var_95"], 0.0)

    def test_get_anomaly_adjustment_success(self):
        expected_mult = round(random.uniform(1.1, 3.0), 2)
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_fallback(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("No detector")):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        mock_response = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=mock_response) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, mock_response)

    def test_export_report_fallback(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("No exporter")):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        random_payload = io.BytesIO(uuid.uuid4().bytes)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=random_payload):
            stream = self.engine.consume_stream()
            self.assertEqual(stream, random_payload)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("No gateway")):
            stream = self.engine.consume_stream()
            self.assertIsNone(stream)


class TestRunMonteCarloStressTestFunction(unittest.TestCase):

    def test_run_monte_carlo_stress_test_execution(self):
        portfolio_id = f"p_{uuid.uuid4().hex[:6]}"
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": round(random.uniform(-0.02, 0.02), 2),
            "horizon_days": random.randint(1, 15)
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()