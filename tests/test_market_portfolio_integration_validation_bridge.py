import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_integration_validation_bridge import (
    MarketPortfolioIntegrationValidationBridge
)
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub


class TestMarketPortfolioIntegrationValidationBridge(unittest.TestCase):

    def setUp(self):
        self.db_storage_path = f"test_db_{uuid.uuid4().hex}.sqlite"
        self.extractor_tool = MagicMock()
        self.market_anomaly_detector = MagicMock()

        self.var_engine = PredictiveVarEngine(
            db_storage=self.db_storage_path,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector
        )
        self.integration_hub = MarketPortfolioIntegrationHub(
            storage_file=self.db_storage_path
        )
        self.validator_bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=self.var_engine,
            integration_hub=self.integration_hub
        )

    def test_run_end_to_end_validation_pipeline_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_code = f"scen_{uuid.uuid4().hex[:6]}"
        url = f"https://{uuid.uuid4().hex[:10]}.market/api/v1/stream"
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        chat_id = str(random.randint(10000000, 99999999))
        shifts = [random.random() for _ in range(3)]

        expected_var_result = {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "var_value": random.uniform(1000.0, 50000.0),
            "status": "VALID"
        }
        expected_hub_result = {
            "status": "SUCCESS",
            "symbol": symbol,
            "processed_shifts": len(shifts)
        }

        with patch.object(self.var_engine, 'calculate_predictive_var', return_value=expected_var_result) as mock_var, \
             patch.object(self.integration_hub, 'run_integrated_pipeline', return_value=expected_hub_result) as mock_hub:

            result = self.validator_bridge.run_end_to_end_validation_pipeline(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                url=url,
                symbol=symbol,
                shifts=shifts,
                telegram_token=telegram_token,
                chat_id=chat_id,
                simulations=random.randint(100, 1000),
                horizon_days=random.randint(1, 30),
                confidence_level=0.95,
                port_value=random.uniform(50000.0, 500000.0),
                scenario_params={"volatility": random.uniform(0.1, 0.5)},
                iterations=random.randint(10, 100)
            )

            mock_var.assert_called_once()
            mock_hub.assert_called_once_with(url, symbol, shifts, telegram_token, chat_id)

            self.assertIn("validation_id", result)
            self.assertEqual(result["var_report"], expected_var_result)
            self.assertEqual(result["integration_report"], expected_hub_result)
            self.assertEqual(result["overall_status"], "PASSED")

    def test_run_stress_validation_bridge_failure(self):
        portfolio_id = f"port_err_{uuid.uuid4().hex[:6]}"
        portfolio_value = random.uniform(10000.0, 99999.0)
        scenario_params = {"shock": random.uniform(-0.5, -0.1)}
        confidence_level = 0.99
        horizon_days = random.randint(5, 15)
        iterations = random.randint(50, 200)

        error_message = f"Simulated Var Engine Failure {uuid.uuid4().hex[:4]}"

        with patch.object(self.var_engine, 'calculate_predictive_stress_var', side_effect=Exception(error_message)) as mock_stress_var:
            with self.assertRaises(Exception) as ctx:
                self.validator_bridge.run_stress_validation_bridge(
                    portfolio_id=portfolio_id,
                    portfolio_value=portfolio_value,
                    scenario_params=scenario_params,
                    confidence_level=confidence_level,
                    horizon_days=horizon_days,
                    iterations=iterations
                )

            mock_stress_var.assert_called_once()
            self.assertIn(error_message, str(ctx.exception))

    def test_stream_validation_audit_export(self):
        stream_data = io.BytesIO(f"stream_payload_{uuid.uuid4().hex}".encode('utf-8'))
        expected_export_result = {
            "audit_id": uuid.uuid4().hex,
            "exported_bytes": stream_data.getbuffer().nbytes,
            "status": "COMPLETED"
        }

        with patch.object(self.var_engine, 'process_market_stream', return_value=True) as mock_process_stream, \
             patch.object(self.integration_hub, 'export_and_dispatch_stream', return_value=expected_export_result) as mock_export:

            response = self.validator_bridge.stream_validation_audit_export(stream_data)

            mock_process_stream.assert_called_once()
            mock_export.assert_called_once()
            self.assertEqual(response, expected_export_result)