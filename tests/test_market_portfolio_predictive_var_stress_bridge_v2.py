import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_predictive_var_stress_bridge_v2 import (
    PredictiveVarStressBridgeV2,
    BridgeExecutionError,
    BridgeValidationError
)
from skills.market_portfolio_predictive_var_engine import VarEngineError, InsufficientDataError
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine


class TestPredictiveVarStressBridgeV2(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.anomaly_detector = MagicMock()
        
        self.bridge = PredictiveVarStressBridgeV2(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.anomaly_detector
        )

        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = "".join(random.choices(string.ascii_uppercase, k=8))
        self.simulations = random.randint(1000, 50000)
        self.horizon_days = random.randint(1, 365)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.portfolio_value = round(random.uniform(10000.0, 10000000.0), 2)
        self.scenario_params = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.random()
            for _ in range(3)
        }
        self.iterations = random.randint(100, 5000)

    def test_execute_combined_risk_pipeline_success(self):
        expected_var_result = {
            "portfolio_id": self.portfolio_id,
            "predictive_var": round(random.uniform(1000.0, 50000.0), 2),
            "confidence": self.confidence_level
        }
        expected_mc_result = {
            "portfolio_id": self.portfolio_id,
            "monte_carlo_stress_loss": round(random.uniform(5000.0, 150000.0), 2),
            "simulations": self.simulations
        }

        with patch('skills.market_portfolio_predictive_var_engine.PredictiveVarEngine.calculate_predictive_var', return_value=expected_var_result) as mock_var, \
             patch('skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.run_simulation', return_value=expected_mc_result) as mock_mc:

            result = self.bridge.execute_combined_risk_pipeline(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.iterations
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("predictive_var_metrics", result)
            self.assertIn("monte_carlo_metrics", result)
            self.assertEqual(result["predictive_var_metrics"], expected_var_result)
            self.assertEqual(result["monte_carlo_metrics"], expected_mc_result)

            mock_var.assert_called_once()
            mock_mc.assert_called_once()

    def test_execute_combined_risk_pipeline_var_engine_error(self):
        err_msg = "".join(random.choices(string.ascii_letters, k=20))
        with patch('skills.market_portfolio_predictive_var_engine.PredictiveVarEngine.calculate_predictive_var', side_effect=VarEngineError(err_msg)) as mock_var:

            with self.assertRaises(BridgeExecutionError) as ctx:
                self.bridge.execute_combined_risk_pipeline(
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days,
                    confidence_level=self.confidence_level,
                    portfolio_value=self.portfolio_value,
                    scenario_params=self.scenario_params,
                    iterations=self.iterations
                )

            self.assertIn(err_msg, str(ctx.exception))
            mock_var.assert_called_once()

    def test_execute_combined_risk_pipeline_insufficient_data_error(self):
        err_msg = "".join(random.choices(string.ascii_letters, k=25))
        with patch('skills.market_portfolio_predictive_var_engine.PredictiveVarEngine.calculate_predictive_var', side_effect=InsufficientDataError(err_msg)) as mock_var:

            with self.assertRaises(BridgeValidationError) as ctx:
                self.bridge.execute_combined_risk_pipeline(
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days,
                    confidence_level=self.confidence_level,
                    portfolio_value=self.portfolio_value,
                    scenario_params=self.scenario_params,
                    iterations=self.iterations
                )

            self.assertIn(err_msg, str(ctx.exception))
            mock_var.assert_called_once()

    def test_bridge_stream_consumption(self):
        stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        stream_mock = io.BytesIO(stream_data)

        expected_processed_stream = {
            "status": "success",
            "bytes_read": len(stream_data)
        }

        with patch('skills.market_portfolio_predictive_var_engine.PredictiveVarEngine.process_market_stream', return_value=expected_processed_stream) as mock_process:

            result = self.bridge.consume_and_bridge_stream(stream_mock)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["bytes_read"], len(stream_data))
            mock_process.assert_called_once_with(stream_mock)

    def test_export_combined_audit_report(self):
        report_id = str(uuid.uuid4())
        loss_limit = round(random.uniform(10000.0, 500000.0), 2)

        var_report = {"report_id": report_id, "var_status": "ok"}
        mc_report = {"report_id": report_id, "mc_status": "ok"}

        with patch('skills.market_portfolio_predictive_var_engine.PredictiveVarEngine.export_predictive_audit_report', return_value=var_report) as mock_var_export, \
             patch('skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.export_report', return_value=mc_report) as mock_mc_export:

            combined_report = self.bridge.export_combined_audit_report(report_id, loss_limit)

            self.assertIsInstance(combined_report, dict)
            self.assertEqual(combined_report["report_id"], report_id)
            self.assertIn("predictive_audit", combined_report)
            self.assertIn("monte_carlo_audit", combined_report)
            self.assertEqual(combined_report["predictive_audit"], var_report)
            self.assertEqual(combined_report["monte_carlo_audit"], mc_report)

            mock_var_export.assert_called_once_with(report_id, loss_limit)
            mock_mc_export.assert_called_once_with(report_id, loss_limit)


if __name__ == '__main__':
    unittest.main()