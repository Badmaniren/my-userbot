import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import requests

from skills.market_portfolio_predictive_var_stress_bridge_v3 import PredictiveVarStressBridge
from skills.market_portfolio_predictive_var_engine import InsufficientDataError, VarEngineError
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import InvalidDataError


class TestPredictiveVarStressBridge(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.bridge = PredictiveVarStressBridge(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector
        )
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        self.simulations = random.randint(100, 5000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.scenario_params = {"param_alpha": random.random()}
        self.iterations = random.randint(10, 100)

    def test_execute_combined_predictive_stress_success(self):
        expected_var = {"var": random.uniform(100.0, 5000.0)}
        expected_stress = {"stress": random.uniform(500.0, 15000.0)}

        with patch.object(self.bridge.var_engine, 'calculate_predictive_var', return_value=expected_var) as mock_var, \
             patch.object(self.bridge.mc_engine, 'run_simulation', return_value=expected_stress) as mock_stress:

            result = self.bridge.execute_combined_predictive_stress(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.iterations
            )

            mock_var.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.iterations
            )
            mock_stress.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )
            self.assertEqual(result["predictive_var"], expected_var)
            self.assertEqual(result["monte_carlo_stress"], expected_stress)

    def test_execute_combined_predictive_stress_fallback_scenario(self):
        invalid_scenario = f"bad_{uuid.uuid4().hex[:6]}"
        expected_var = {"recovered_var": random.uniform(10.0, 1000.0)}
        expected_stress = {"recovered_stress": random.uniform(50.0, 5000.0)}

        with patch.object(self.bridge.var_engine, 'calculate_predictive_var', side_effect=[InsufficientDataError("Fail"), expected_var]) as mock_var, \
             patch.object(self.bridge.mc_engine, 'run_simulation', return_value=expected_stress) as mock_stress:

            result = self.bridge.execute_combined_predictive_stress(
                portfolio_id=self.portfolio_id,
                scenario_code=invalid_scenario,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.iterations
            )

            self.assertEqual(mock_var.call_count, 2)
            self.assertEqual(result["predictive_var"], expected_var)
            self.assertEqual(result["monte_carlo_stress"], expected_stress)

    def test_execute_combined_predictive_stress_unrecoverable_error(self):
        valid_bad_scenario = f"SCENARIO_{uuid.uuid4().hex[:6]}"
        with patch.object(self.bridge.var_engine, 'calculate_predictive_var', side_effect=InvalidDataError("Critical")):
            with self.assertRaises(InvalidDataError):
                self.bridge.execute_combined_predictive_stress(
                    portfolio_id=self.portfolio_id,
                    scenario_code=valid_bad_scenario,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days,
                    confidence_level=self.confidence_level,
                    portfolio_value=self.portfolio_value,
                    scenario_params=self.scenario_params,
                    iterations=self.iterations
                )

    def test_fetch_and_bridge_external_metrics(self):
        target_url = f"https://api.{uuid.uuid4().hex[:8]}.org/metrics"
        expected_json = {"metric_id": uuid.uuid4().hex, "value": random.random()}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_json
        mock_response.raise_for_status.return_value = None

        with patch('requests.get', return_value=mock_response) as mock_get:
            res = self.bridge.fetch_and_bridge_external_metrics(target_url, self.portfolio_id, self.scenario_code)
            mock_get.assert_called_once_with(target_url, timeout=10)
            self.assertEqual(res, expected_json)

    def test_evaluate_bridge_risk_anomaly(self):
        soup_content = f"<html><body><span>{uuid.uuid4().hex}</span></body></html>"
        expected_eval = {"anomaly_detected": False, "score": random.random()}

        with patch.object(self.bridge.var_engine, 'evaluate_risk_anomaly', return_value=expected_eval) as mock_eval:
            res = self.bridge.evaluate_bridge_risk_anomaly(self.portfolio_id, self.scenario_code, soup_content)
            mock_eval.assert_called_once_with(self.portfolio_id, self.scenario_code, soup_content)
            self.assertEqual(res, expected_eval)

    def test_process_bridge_market_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        expected_res = {"stream_status": "processed"}

        with patch.object(self.bridge.var_engine, 'process_market_stream', return_value=expected_res) as mock_stream:
            res = self.bridge.process_bridge_market_stream(stream_data)
            mock_stream.assert_called_once_with(stream_data)
            self.assertEqual(res, expected_res)

    def test_export_bridge_audit_report(self):
        report_id = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        expected_report = {"report_id": report_id, "status": "exported"}

        with patch.object(self.bridge.var_engine, 'export_predictive_audit_report', return_value=expected_report) as mock_export:
            res = self.bridge.export_bridge_audit_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_report)

    def test_execute_stress_monte_carlo(self):
        expected_mc = {"mc_result": random.uniform(100.0, 9999.0)}
        with patch.object(self.bridge.mc_engine, 'run_simulation', return_value=expected_mc) as mock_run:
            res = self.bridge.execute_stress_monte_carlo(self.portfolio_id, self.simulations, self.horizon_days)
            mock_run.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )
            self.assertEqual(res, expected_mc)

    def test_generate_comprehensive_risk_report(self):
        report_id = f"comp_{uuid.uuid4().hex[:6]}"
        loss_limit = round(random.uniform(5000.0, 100000.0), 2)

        var_mock_ret = {"var_value": random.uniform(10.0, 500.0)}
        stress_mock_ret = {"monte_carlo_result": random.uniform(20.0, 1000.0)}

        with patch.object(self.bridge, 'execute_predictive_var', return_value=var_mock_ret) as mock_var_exec, \
             patch.object(self.bridge, 'execute_stress_monte_carlo', return_value=stress_mock_ret) as mock_stress_exec:

            report = self.bridge.generate_comprehensive_risk_report(
                report_id=report_id,
                loss_limit=loss_limit,
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.iterations
            )

            self.assertEqual(report["report_id"], report_id)
            self.assertEqual(report["loss_limit"], loss_limit)
            self.assertEqual(report["predictive_var"], var_mock_ret)
            self.assertEqual(report["stress_monte_carlo"], stress_mock_ret)

    def test_cleanup(self):
        try:
            self.bridge.cleanup()
        except Exception as e:
            self.fail(f"Cleanup raised an unexpected exception: {e}")