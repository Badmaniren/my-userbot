import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
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
from skills import market_portfolio_audit_compliance_hub


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex}"
        self.report_id = f"rep_{uuid.uuid4().hex}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.loss_limit = round(random.uniform(1000.0, 10000.0), 2)

    def test_run_simulation_with_db_storage(self):
        engine = MonteCarloStressEngine()
        portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_data) as mock_fetch, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:
            
            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_audit.assert_called_once()
            
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_attribute_error_fallback(self):
        engine = MonteCarloStressEngine()
        
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch")):
            if not hasattr(db_storage, "_in_memory_db"):
                setattr(db_storage, "_in_memory_db", {})
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
            
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_success(self):
        engine = MonteCarloStressEngine()
        expected_mult = round(random.uniform(1.1, 2.5), 2)

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult) as mock_detector:
            mult = engine._get_anomaly_adjustment()
            mock_detector.assert_called_once()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("No attr")):
            mult = engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        engine = MonteCarloStressEngine()
        expected_response = {"report_id": self.report_id, "loss_limit": self.loss_limit, "status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            res = engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_response)

    def test_export_report_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("No export")):
            res = engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(res["report_id"], self.report_id)
            self.assertEqual(res["loss_limit"], self.loss_limit)

    def test_consume_stream_success(self):
        engine = MonteCarloStressEngine()
        payload = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=payload) as mock_stream:
            res = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, payload)

    def test_consume_stream_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("No stream")):
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        iterations = random.randint(15, 30)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:
            result = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_audit.assert_called_once()
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["initial_value"], self.initial_value)
            self.assertEqual(result["iterations"], iterations)
            self.assertIn("simulation_id", result)
            self.assertTrue(result["simulation_id"].startswith("sim_"))
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()