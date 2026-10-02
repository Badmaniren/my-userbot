import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success_and_math_integrity(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 10)
        initial_val = float(random.randint(50000, 200000))
        vol = random.uniform(0.1, 0.4)
        drift_val = random.uniform(-0.05, 0.05)

        mock_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": vol,
            "drift": drift_val
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            
            self.assertEqual(len(result["simulation_results"]), simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), horizon_days)

            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db_and_anomaly(self):
        portfolio_id = f"fallback_{uuid.uuid4().hex}"
        simulations = random.randint(5, 20)
        horizon_days = random.randint(1, 5)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertGreaterEqual(result["var_95"], 0.0)
            self.assertGreaterEqual(result["cvar_95"], 0.0)

    def test_export_report_methods(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 50000))

        with patch("skills.market_portfolio_data_exporter.export", return_value={"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}) as mock_export:
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_methods(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_io = io.BytesIO(stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=mock_io) as mock_stream:
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res.read(), stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_functional(self):
        portfolio_id = f"stress_{uuid.uuid4().hex}"
        portfolio_value = float(random.randint(10000, 500000))
        iterations = random.randint(20, 100)
        
        scenario_params = {
            "volatility": random.uniform(0.15, 0.5),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 15)
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()