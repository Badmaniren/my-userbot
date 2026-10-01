import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 5)
        
        mock_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": float(random.randint(50000, 150000)),
            "volatility": 0.15,
            "drift": 0.02
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.1) as mock_anomaly:
            
            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_attribute_error_fallback(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(10, 30)
        horizon_days = random.randint(1, 3)

        initial_val = float(random.randint(10000, 50000))

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch method")) as mock_fetch, \
             patch("skills.db_storage._in_memory_db", {portfolio_id: {"initial_value": initial_val}}, create=True), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("No anomaly")):
            
            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_export_report(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = float(random.randint(1000, 10000))

        expected_response = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)

            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_response)

    def test_export_report_attribute_error(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = float(random.randint(1000, 10000))

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)

            self.assertEqual(res, {"report_id": report_id, "loss_limit": loss_limit})

    def test_consume_stream(self):
        payload_data = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=payload_data) as mock_stream:
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()

            mock_stream.assert_called_once()
            self.assertEqual(res, payload_data)

    def test_consume_stream_attribute_error(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()

            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        portfolio_id = f"pid_{uuid.uuid4().hex[:8]}"
        portfolio_value = float(random.randint(50000, 200000))
        iterations = random.randint(20, 60)
        scenario_params = {
            "volatility": 0.25,
            "drift": -0.05,
            "horizon_days": random.randint(1, 10)
        }

        res = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertIn("simulation_id", res)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["initial_value"], portfolio_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()