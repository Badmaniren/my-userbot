import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine,
    VarEngineError,
    InsufficientDataError
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine
)
import skills.market_portfolio_predictive_var_stress_bridge_v3 as bridge_module


class TestMarketPortfolioPredictiveVarStressBridgeV3(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = "".join(random.choices(string.ascii_uppercase, k=8))
        self.simulations = random.randint(100, 5000)
        self.horizon_days = random.randint(1, 90)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.portfolio_value = round(random.uniform(10000.0, 10000000.0), 2)
        self.loss_limit = round(random.uniform(1000.0, 500000.0), 2)
        self.report_id = str(uuid.uuid4())
        self.scenario_id = str(uuid.uuid4())
        self.base_multiplier = round(random.uniform(0.5, 3.0), 2)
        self.target_url = f"https://{uuid.uuid4().hex}.com/api/v1/metrics"
        
        self.scenario_params = {
            "volatility_multiplier": round(random.uniform(1.0, 5.0), 2),
            "market_shock": round(random.uniform(-0.5, -0.01), 4),
            "liquidity_factor": round(random.uniform(0.1, 1.0), 2)
        }
        self.scenario_data = {
            "stress_scenario": self.scenario_code,
            "drop_rate": round(random.uniform(0.01, 0.3), 4)
        }
        self.monte_carlo_metrics = {
            "mean_loss": round(random.uniform(100.0, 5000.0), 2),
            "max_drawdown": round(random.uniform(0.05, 0.5), 4)
        }

    def test_bridge_initialization_and_composition(self):
        db_storage_mock = MagicMock()
        extractor_mock = MagicMock()
        anomaly_detector_mock = MagicMock()

        bridge_instance = bridge_module.PredictiveVarStressBridge(
            db_storage=db_storage_mock,
            extractor_tool=extractor_mock,
            market_anomaly_detector=anomaly_detector_mock
        )

        self.assertIsInstance(bridge_instance.var_engine, PredictiveVarEngine)
        self.assertIsInstance(bridge_instance.mc_engine, MonteCarloStressEngine)
        self.assertEqual(bridge_instance.db_storage, db_storage_mock)

    def test_execute_combined_predictive_stress_success(self):
        expected_var = round(random.uniform(500.0, 50000.0), 2)
        expected_mc_res = {
            str(uuid.uuid4()): round(random.uniform(100.0, 10000.0), 2),
            "status": "".join(random.choices(string.ascii_lowercase, k=6))
        }

        with patch("skills.market_portfolio_predictive_var_stress_bridge_v3.PredictiveVarEngine.calculate_predictive_var", return_value=expected_var) as mock_var, \
             patch("skills.market_portfolio_predictive_var_stress_bridge_v3.MonteCarloStressEngine.run_simulation", return_value=expected_mc_res) as mock_mc:

            db_storage_mock = MagicMock()
            extractor_mock = MagicMock()
            anomaly_detector_mock = MagicMock()

            bridge_instance = bridge_module.PredictiveVarStressBridge(
                db_storage=db_storage_mock,
                extractor_tool=extractor_mock,
                market_anomaly_detector=anomaly_detector_mock
            )

            result = bridge_instance.execute_combined_predictive_stress(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.simulations
            )

            mock_var.assert_called_once()
            mock_mc.assert_called_once()
            self.assertIn("predictive_var", result)
            self.assertIn("monte_carlo_stress", result)
            self.assertEqual(result["predictive_var"], expected_var)
            self.assertEqual(result["monte_carlo_stress"], expected_mc_res)

    def test_execute_combined_predictive_stress_var_error_handling(self):
        err_message = uuid.uuid4().hex

        with patch("skills.market_portfolio_predictive_var_stress_bridge_v3.PredictiveVarEngine.calculate_predictive_var", side_effect=VarEngineError(err_message)) as mock_var:

            db_storage_mock = MagicMock()
            extractor_mock = MagicMock()
            anomaly_detector_mock = MagicMock()

            bridge_instance = bridge_module.PredictiveVarStressBridge(
                db_storage=db_storage_mock,
                extractor_tool=extractor_mock,
                market_anomaly_detector=anomaly_detector_mock
            )

            with self.assertRaises(VarEngineError) as ctx:
                bridge_instance.execute_combined_predictive_stress(
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days,
                    confidence_level=self.confidence_level,
                    portfolio_value=self.portfolio_value,
                    scenario_params=self.scenario_params,
                    iterations=self.simulations
                )
            self.assertIn(err_message, str(ctx.exception))
            mock_var.assert_called_once()

    def test_bridge_fetch_external_metrics_with_network_error(self):
        db_storage_mock = MagicMock()
        extractor_mock = MagicMock()
        anomaly_detector_mock = MagicMock()

        bridge_instance = bridge_module.PredictiveVarStressBridge(
            db_storage=db_storage_mock,
            extractor_tool=extractor_mock,
            market_anomaly_detector=anomaly_detector_mock
        )

        with patch("requests.get", side_effect=requests.RequestException("Network Failure")) as mock_get:
            with self.assertRaises(requests.RequestException):
                bridge_instance.fetch_and_bridge_external_metrics(
                    target_url=self.target_url,
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code
                )
            mock_get.assert_called_once_with(self.target_url, timeout=10)

    def test_bridge_evaluate_anomaly_with_soup(self):
        db_storage_mock = MagicMock()
        extractor_mock = MagicMock()
        anomaly_detector_mock = MagicMock()

        bridge_instance = bridge_module.PredictiveVarStressBridge(
            db_storage=db_storage_mock,
            extractor_tool=extractor_mock,
            market_anomaly_detector=anomaly_detector_mock
        )

        random_html_text = f"<html><body><div id='{uuid.uuid4().hex}'>{uuid.uuid4().hex}</div></body></html>"
        soup = BeautifulSoup(random_html_text, "html.parser")
        expected_eval_result = {"anomaly_detected": True, "score": random.random()}

        with patch.object(bridge_instance.var_engine, "evaluate_risk_anomaly", return_value=expected_eval_result) as mock_eval:
            res = bridge_instance.evaluate_bridge_risk_anomaly(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                soup_content=soup
            )
            mock_eval.assert_called_once_with(self.portfolio_id, self.scenario_code, soup)
            self.assertEqual(res, expected_eval_result)

    def test_stream_processing_pipeline_with_bytes_io(self):
        db_storage_mock = MagicMock()
        extractor_mock = MagicMock()
        anomaly_detector_mock = MagicMock()

        bridge_instance = bridge_module.PredictiveVarStressBridge(
            db_storage=db_storage_mock,
            extractor_tool=extractor_mock,
            market_anomaly_detector=anomaly_detector_mock
        )

        random_stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(random_stream_data)

        expected_response = {"processed": True, "bytes_read": len(random_stream_data)}

        with patch.object(bridge_instance.var_engine, "process_market_stream", return_value=expected_response) as mock_process:
            res = bridge_instance.process_bridge_market_stream(stream_mock)
            mock_process.assert_called_once_with(stream_mock)
            self.assertEqual(res, expected_response)

    def test_export_bridge_audit_report(self):
        db_storage_mock = MagicMock()
        extractor_mock = MagicMock()
        anomaly_detector_mock = MagicMock()

        bridge_instance = bridge_module.PredictiveVarStressBridge(
            db_storage=db_storage_mock,
            extractor_tool=extractor_mock,
            market_anomaly_detector=anomaly_detector_mock
        )

        expected_report = {
            "report_id": self.report_id,
            "loss_limit": self.loss_limit,
            "status": "APPROVED"
        }

        with patch.object(bridge_instance.var_engine, "export_predictive_audit_report", return_value=expected_report) as mock_export:
            res = bridge_instance.export_bridge_audit_report(
                report_id=self.report_id,
                loss_limit=self.loss_limit
            )
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_report)