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
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = random.uniform(50000.0, 500000.0)
        self.volatility = random.uniform(0.1, 0.5)
        self.drift = random.uniform(-0.05, 0.05)
        
        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_run_simulation_structure_and_logic(self):
        simulations = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

        result = self.engine.run_simulation(self.portfolio_id, simulations, horizon_days)

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), simulations)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), horizon_days)
        
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_run_simulation_with_anomaly_detector_mock(self):
        simulations = random.randint(10, 50)
        horizon_days = random.randint(2, 10)
        random_mult = random.uniform(1.5, 3.0)

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=random_mult) as mock_anomaly:
            result = self.engine.run_simulation(self.portfolio_id, simulations, horizon_days)
            mock_anomaly.assert_called_once()
            self.assertIn("var_95", result)

    def test_export_report_delegation(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = random.uniform(1000.0, 15000.0)

        expected_response = {"report_id": report_id, "loss_limit": loss_limit, "status": f"exported_{uuid.uuid4().hex[:4]}"}
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_response)

    def test_consume_stream_integration(self):
        mock_payload = io.BytesIO(f"stream_data_{uuid.uuid4().hex}".encode('utf-8'))
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=mock_payload) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, mock_payload)


class TestStandaloneMonteCarloStressTest(unittest.TestCase):

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_id = f"port_fn_{uuid.uuid4().hex[:8]}"
        portfolio_value = random.uniform(10000.0, 1000000.0)
        iterations = random.randint(100, 300)
        scenario_params = {
            "volatility": random.uniform(0.15, 0.45),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 15)
        }

        res = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertIn("simulation_id", res)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["initial_value"], portfolio_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("var_95", res)
        self.assertIn("expected_shortfall", res)
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()