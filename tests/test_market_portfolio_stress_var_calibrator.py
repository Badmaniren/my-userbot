import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string
import sys
import types

from skills import market_portfolio_stress_var_calibrator

class TestMarketPortfolioStressVarCalibrator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.mc_engine = MagicMock()
        self.var_core = MagicMock()

        self.calibrator = market_portfolio_stress_var_calibrator.MarketPortfolioStressVarCalibrator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            market_portfolio_stress_monte_carlo_engine=self.mc_engine,
            market_portfolio_var_liquidity_core=self.var_core
        )

    def test_calibration_execution_flow(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        simulations_count = random.randint(1000, 50000)

        expected_var = round(random.uniform(1000.0, 500000.0), 2)
        expected_stress = round(random.uniform(50000.0, 2000000.0), 2)

        self.mc_engine.run_simulation.return_value = {
            "status": "success",
            "iterations": simulations_count,
            "raw_outcomes": [random.uniform(-0.1, 0.05) for _ in range(10)]
        }

        self.var_core.calculate_var.return_value = {
            "var_value": expected_var,
            "confidence": confidence_level
        }

        result = self.calibrator.calibrate_portfolio_var_and_stress(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level,
            simulations_count=simulations_count
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_result"]["var_value"], expected_var)
        self.mc_engine.run_simulation.assert_called_once()
        self.var_core.calculate_var.assert_called_once()
        self.db_storage.save_calibration_metrics.assert_called_once()

    def test_stress_scenario_calibration_anomaly(self):
        portfolio_id = str(uuid.uuid4())
        anomaly_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.uniform(10.0, 999.9)

        self.extractor_1.fetch_metrics.return_value = {
            anomaly_metric_name: metric_value
        }

        with patch('skills.market_portfolio_stress_var_calibrator.io.BytesIO') as mock_io_class:
            mock_stream = MagicMock()
            mock_stream.read.return_value = bytes(''.join(random.choices(string.ascii_letters, k=50)), 'utf-8')
            mock_io_class.return_value = mock_stream

            evaluated_stress = self.calibrator.evaluate_external_stress_factor(
                portfolio_id=portfolio_id,
                metric_key=anomaly_metric_name
            )

            self.assertIn("stress_score", evaluated_stress)
            self.assertEqual(evaluated_stress["portfolio_id"], portfolio_id)
            self.extractor_1.fetch_metrics.assert_called_once_with(anomaly_metric_name)

    def test_calibrator_empty_simulation_handling(self):
        portfolio_id = str(uuid.uuid4())
        self.mc_engine.run_simulation.return_value = None

        with self.assertRaises(ValueError):
            self.calibrator.calibrate_portfolio_var_and_stress(
                portfolio_id=portfolio_id,
                confidence_level=0.99,
                simulations_count=100
            )

    def test_batch_calibration_dispatch(self):
        portfolios = [str(uuid.uuid4()) for _ in range(3)]

        self.mc_engine.run_simulation.side_effect = [
            {"status": "ok", "iterations": 500},
            {"status": "ok", "iterations": 500},
            {"status": "ok", "iterations": 500}
        ]

        results = self.calibrator.batch_calibrate(portfolios)

        self.assertEqual(len(results), 3)
        for i, res in enumerate(results):
            self.assertEqual(res["portfolio_id"], portfolios[i])
            self.assertEqual(res["status"], "calibrated")