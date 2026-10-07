import unittest
from unittest.mock import patch
import uuid
import random
import io
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMarketPortfolioStressMonteCarloEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 10)
        initial_val = round(random.uniform(10000.0, 500000.0), 2)

        engine = MonteCarloStressEngine()

        with patch("skills.db_storage.fetch_portfolio") as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:
            
            mock_fetch.return_value = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_val,
                "volatility": 0.15,
                "drift": 0.05
            }

            with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:
                result = engine.run_simulation(portfolio_id, simulations, horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations)

    def test_run_simulation_attribute_error_fallback(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(5, 20)
        horizon_days = random.randint(1, 5)

        engine = MonteCarloStressEngine()

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch")):
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(len(result["simulation_results"]), simulations)

    def test_export_report(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_data_exporter.export") as mock_export:
            mock_export.return_value = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}
            res = engine.export_report(report_id, loss_limit)

        self.assertEqual(res["report_id"], report_id)
        self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream(self):
        engine = MonteCarloStressEngine()
        payload_key = uuid.uuid4().hex

        with patch("skills.market_portfolio_api_gateway.stream_payload") as mock_stream:
            mock_stream.return_value = {"data": payload_key}
            res = engine.consume_stream()

        self.assertIsInstance(res, dict)
        self.assertEqual(res["data"], payload_key)


class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def test_run_monte_carlo_stress_test(self):
        portfolio_id = f"p_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        iterations = random.randint(20, 100)
        volatility = round(random.uniform(0.1, 0.4), 2)
        drift = round(random.uniform(-0.05, 0.05), 2)
        horizon_days = random.randint(1, 15)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(
                portfolio_id=portfolio_id,
                portfolio_value=initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["initial_value"], initial_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("var_95", res)
        self.assertIn("expected_shortfall", res)
        self.assertIn("simulation_id", res)
        mock_log.assert_called_once()
        mock_vis.assert_called_once()