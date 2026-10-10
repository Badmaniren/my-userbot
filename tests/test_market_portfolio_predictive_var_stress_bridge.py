import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_predictive_var_stress_bridge import (
    PredictiveVarStressBridge,
    PredictiveVarStressBridgeError
)

class TestPredictiveVarStressBridge(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.extractor_mock = MagicMock()
        self.anomaly_detector_mock = MagicMock()
        
        self.bridge = PredictiveVarStressBridge(
            db_storage=self.db_storage_mock,
            extractor_tool=self.extractor_mock,
            market_anomaly_detector=self.anomaly_detector_mock
        )

    def test_run_predictive_stress_bridge_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = "".join(random.choices(string.ascii_uppercase, k=6))
        simulations = random.randint(100, 5000)
        horizon_days = random.randint(1, 90)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        portfolio_value = round(random.uniform(10000.0, 5000000.0), 2)
        
        var_result = round(random.uniform(500.0, 50000.0), 2)
        mc_result = {
            "simulation_id": uuid.uuid4().hex,
            "expected_shortfall": round(random.uniform(1000.0, 100000.0), 2),
            "max_drawdown": round(random.uniform(0.05, 0.50), 4)
        }

        with patch("skills.market_portfolio_predictive_var_stress_bridge.PredictiveVarEngine") as mock_var_engine_cls, \
             patch("skills.market_portfolio_predictive_var_stress_bridge.MonteCarloStressEngine") as mock_mc_engine_cls:

            mock_var_instance = mock_var_engine_cls.return_value
            mock_var_instance.calculate_predictive_var.return_value = {"var_value": var_result}

            mock_mc_instance = mock_mc_engine_cls.return_value
            mock_mc_instance.run_simulation.return_value = mc_result

            result = self.bridge.execute_stress_bridge(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario_code"], scenario_code)
            self.assertEqual(result["predictive_var"], var_result)
            self.assertEqual(result["monte_carlo_metrics"], mc_result)

            mock_var_instance.calculate_predictive_var.assert_called_once_with(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=None,
                iterations=simulations
            )
            mock_mc_instance.run_simulation.assert_called_once_with(
                portfolio_id=portfolio_id,
                simulations=simulations,
                horizon_days=horizon_days
            )

    def test_run_predictive_stress_bridge_var_failure(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = "".join(random.choices(string.ascii_uppercase, k=5))
        simulations = random.randint(10, 100)
        horizon_days = random.randint(1, 10)
        confidence_level = round(random.uniform(0.90, 0.99), 2)
        portfolio_value = round(random.uniform(1000.0, 50000.0), 2)

        error_message = f"VarEngineError_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_predictive_var_stress_bridge.PredictiveVarEngine") as mock_var_engine_cls:
            mock_var_instance = mock_var_engine_cls.return_value
            mock_var_instance.calculate_predictive_var.side_effect = Exception(error_message)

            with self.assertRaises(PredictiveVarStressBridgeError) as ctx:
                self.bridge.execute_stress_bridge(
                    portfolio_id=portfolio_id,
                    scenario_code=scenario_code,
                    simulations=simulations,
                    horizon_days=horizon_days,
                    confidence_level=confidence_level,
                    portfolio_value=portfolio_value
                )

            self.assertIn(error_message, str(ctx.exception))

    def test_consume_stream_integration(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(stream_data)

        with patch("skills.market_portfolio_predictive_var_stress_bridge.PredictiveVarEngine") as mock_var_engine_cls:
            mock_var_instance = mock_var_engine_cls.return_value
            
            self.bridge.consume_and_process_stream(stream_mock)

            mock_var_instance.process_market_stream.assert_called_once()

    def test_export_stress_bridge_audit_report(self):
        report_id = uuid.uuid4().hex
        loss_limit = round(random.uniform(1000.0, 1000000.0), 2)
        expected_report = {
            "report_id": report_id,
            "loss_limit": loss_limit,
            "status": "APPROVED",
            "token": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_predictive_var_stress_bridge.PredictiveVarEngine") as mock_var_engine_cls, \
             patch("skills.market_portfolio_predictive_var_stress_bridge.MonteCarloStressEngine") as mock_mc_engine_cls:

            mock_var_instance = mock_var_engine_cls.return_value
            mock_var_instance.export_predictive_audit_report.return_value = expected_report

            mock_mc_instance = mock_mc_engine_cls.return_value
            mock_mc_instance.export_report.return_value = {"mc_audit": uuid.uuid4().hex}

            report = self.bridge.export_combined_audit_report(report_id=report_id, loss_limit=loss_limit)

            self.assertEqual(report["predictive_report"], expected_report)
            self.assertIn("monte_carlo_report", report)

            mock_var_instance.export_predictive_audit_report.assert_called_once_with(report_id, loss_limit)
            mock_mc_instance.export_report.assert_called_once_with(report_id, loss_limit)

    def test_evaluate_risk_anomaly_bridge(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = "".join(random.choices(string.ascii_uppercase, k=4))
        soup_content = f"<html><body><span>{uuid.uuid4().hex}</span></body></html>"

        expected_anomaly_result = {
            "anomaly_detected": random.choice([True, False]),
            "score": round(random.uniform(0.0, 1.0), 2)
        }

        with patch("skills.market_portfolio_predictive_var_stress_bridge.PredictiveVarEngine") as mock_var_engine_cls:
            mock_var_instance = mock_var_engine_cls.return_value
            mock_var_instance.evaluate_risk_anomaly.return_value = expected_anomaly_result

            result = self.bridge.evaluate_anomaly(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                soup_content=soup_content
            )

            self.assertEqual(result, expected_anomaly_result)
            mock_var_instance.evaluate_risk_anomaly.assert_called_once_with(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                soup_content=soup_content
            )