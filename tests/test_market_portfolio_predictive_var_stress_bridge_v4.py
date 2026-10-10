import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_predictive_var_stress_bridge_v4 import (
    PredictiveVarStressBridgeV4,
    BridgeExecutionError,
    BridgeValidationError
)


class TestPredictiveVarStressBridgeV4(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.extractor_mock = MagicMock()
        self.anomaly_detector_mock = MagicMock()
        
        self.bridge = PredictiveVarStressBridgeV4(
            db_storage=self.db_storage_mock,
            extractor_tool=self.extractor_mock,
            market_anomaly_detector=self.anomaly_detector_mock
        )

    def test_run_comprehensive_stress_pipeline_success(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(100, 1000)
        horizon_days = random.randint(1, 30)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        scenario_params = {"shock": random.uniform(-0.5, -0.1)}
        iterations = random.randint(10, 100)

        expected_var_result = {
            "portfolio_id": portfolio_id,
            "predictive_var": round(random.uniform(1000.0, 50000.0), 2),
            "confidence": confidence_level
        }
        expected_mc_result = {
            "portfolio_id": portfolio_id,
            "simulations_run": simulations,
            "max_drawdown": round(random.uniform(0.05, 0.40), 4)
        }

        with patch("skills.market_portfolio_predictive_var_stress_bridge_v4.PredictiveVarEngine") as MockVarEngineClass, \
             patch("skills.market_portfolio_predictive_var_stress_bridge_v4.MonteCarloStressEngine") as MockMcEngineClass:
            
            mock_var_instance = MockVarEngineClass.return_value
            mock_var_instance.calculate_predictive_var.return_value = expected_var_result

            mock_mc_instance = MockMcEngineClass.return_value
            mock_mc_instance.run_simulation.return_value = expected_mc_result

            result = self.bridge.run_comprehensive_stress_pipeline(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["var_metrics"], expected_var_result)
            self.assertEqual(result["monte_carlo_metrics"], expected_mc_result)
            self.assertIn("execution_id", result)

            mock_var_instance.calculate_predictive_var.assert_called_once_with(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )
            mock_mc_instance.run_simulation.assert_called_once_with(
                portfolio_id=portfolio_id,
                simulations=simulations,
                horizon_days=horizon_days
            )

    def test_run_comprehensive_stress_pipeline_var_failure(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(100, 1000)
        horizon_days = random.randint(1, 30)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        scenario_params = {"shock": random.uniform(-0.5, -0.1)}
        iterations = random.randint(10, 100)

        error_msg = f"VarEngineError_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_predictive_var_stress_bridge_v4.PredictiveVarEngine") as MockVarEngineClass:
            mock_var_instance = MockVarEngineClass.return_value
            mock_var_instance.calculate_predictive_var.side_effect = Exception(error_msg)

            with self.assertRaises(BridgeExecutionError) as ctx:
                self.bridge.run_comprehensive_stress_pipeline(
                    portfolio_id=portfolio_id,
                    scenario_code=scenario_code,
                    simulations=simulations,
                    horizon_days=horizon_days,
                    confidence_level=confidence_level,
                    portfolio_value=portfolio_value,
                    scenario_params=scenario_params,
                    iterations=iterations
                )
            
            self.assertIn(error_msg, str(ctx.exception))

    def test_process_stream_and_bridge_audit(self):
        report_id = str(uuid.uuid4())
        loss_limit = round(random.uniform(5000.0, 50000.0), 2)
        stream_data_bytes = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(stream_data_bytes)

        expected_audit_report = {
            "report_id": report_id,
            "status": "APPROVED",
            "loss_limit": loss_limit
        }

        with patch("skills.market_portfolio_predictive_var_stress_bridge_v4.PredictiveVarEngine") as MockVarEngineClass, \
             patch("skills.market_portfolio_predictive_var_stress_bridge_v4.MonteCarloStressEngine") as MockMcEngineClass:
            
            mock_var_instance = MockVarEngineClass.return_value
            mock_var_instance.export_predictive_audit_report.return_value = expected_audit_report

            mock_mc_instance = MockMcEngineClass.return_value
            mock_mc_instance.consume_stream.return_value = {"consumed": True}

            result = self.bridge.process_stream_and_bridge_audit(
                stream_mock=stream_mock,
                report_id=report_id,
                loss_limit=loss_limit
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["audit_report"], expected_audit_report)
            self.assertEqual(result["report_id"], report_id)

            mock_var_instance.process_market_stream.assert_called_once_with(stream_mock)
            mock_var_instance.export_predictive_audit_report.assert_called_once_with(report_id, loss_limit)
            mock_mc_instance.consume_stream.assert_called_once()

    def test_validate_bridge_inputs_raises_validation_error(self):
        invalid_portfolio_id = 12345
        scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(100, 1000)
        horizon_days = random.randint(1, 30)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        scenario_params = {}
        iterations = random.randint(10, 100)

        with self.assertRaises(BridgeValidationError):
            self.bridge.run_comprehensive_stress_pipeline(
                portfolio_id=invalid_portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )


if __name__ == '__main__':
    unittest.main()