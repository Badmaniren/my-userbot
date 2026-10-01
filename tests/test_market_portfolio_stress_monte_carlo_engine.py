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


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 150000.0)
        self.volatility = random.uniform(0.1, 0.4)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_with_db_storage_mock(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }
        
        with patch.object(db_storage, "fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch:
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
            
            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), self.horizon_days)

    def test_run_simulation_fallback_in_memory_db(self):
        with patch.object(db_storage, "fetch_portfolio", side_effect=AttributeError):
            db_storage._in_memory_db = {
                self.portfolio_id: {
                    "portfolio_id": self.portfolio_id,
                    "initial_value": self.initial_value,
                    "volatility": self.volatility,
                    "drift": self.drift
                }
            }
            
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
            
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_get_anomaly_adjustment_success(self):
        expected_mult = random.uniform(1.1, 2.5)
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", return_value=expected_mult) as mock_detector:
            mult = self.engine._get_anomaly_adjustment()
            mock_detector.assert_called_once()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_fallback(self):
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)
        expected_export_result = {"status": uuid.uuid4().hex, "report_id": report_id, "loss_limit": loss_limit}
        
        with patch.object(market_portfolio_data_exporter, "export", return_value=expected_export_result) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_export_result)

    def test_export_report_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)
        with patch.object(market_portfolio_data_exporter, "export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res, {"report_id": report_id, "loss_limit": loss_limit})

    def test_consume_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        with patch.object(market_portfolio_api_gateway, "stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_consume_stream_fallback(self):
        with patch.object(market_portfolio_api_gateway, "stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(20, 60)

        result = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

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