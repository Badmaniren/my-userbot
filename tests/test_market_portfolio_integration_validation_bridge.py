import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_integration_validation_bridge import MarketPortfolioIntegrationValidationBridge

class TestMarketPortfolioIntegrationValidationBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.scenario_code = uuid.uuid4().hex
        self.url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.symbol = uuid.uuid4().hex.upper()[:5]
        self.shifts = [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)]
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.simulations = random.randint(100, 1000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.9, 0.99), 2)
        self.port_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.scenario_params = {uuid.uuid4().hex: random.random()}
        self.iterations = random.randint(5, 50)

    def test_init_default_dependencies(self):
        db_storage = f"{uuid.uuid4().hex}.sqlite"
        bridge = MarketPortfolioIntegrationValidationBridge(db_storage=db_storage)
        self.assertIsNotNone(bridge.var_engine)
        self.assertIsNotNone(bridge.integration_hub)

    def test_init_custom_dependencies(self):
        mock_var_engine = MagicMock()
        mock_integration_hub = MagicMock()
        bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=mock_var_engine,
            integration_hub=mock_integration_hub
        )
        self.assertEqual(bridge.var_engine, mock_var_engine)
        self.assertEqual(bridge.integration_hub, mock_integration_hub)

    def test_run_end_to_end_validation_pipeline(self):
        mock_var_engine = MagicMock()
        expected_var_report = {
            "portfolio_id": self.portfolio_id,
            "scenario_code": self.scenario_code,
            "var_value": round(random.uniform(100.0, 5000.0), 2),
            "status": "OK"
        }
        mock_var_engine.calculate_predictive_var.return_value = expected_var_report

        mock_integration_hub = MagicMock()
        expected_integration_report = {
            "status": "SUCCESS",
            "pipeline_id": uuid.uuid4().hex
        }
        mock_integration_hub.run_integrated_pipeline.return_value = expected_integration_report

        bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=mock_var_engine,
            integration_hub=mock_integration_hub
        )

        result = bridge.run_end_to_end_validation_pipeline(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            port_value=self.port_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )

        mock_var_engine.calculate_predictive_var.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.port_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )

        mock_integration_hub.run_integrated_pipeline.assert_called_once_with(
            self.url, self.symbol, self.shifts, self.telegram_token, self.chat_id
        )

        self.assertIn("validation_id", result)
        self.assertEqual(result["var_report"], expected_var_report)
        self.assertEqual(result["integration_report"], expected_integration_report)
        self.assertEqual(result["overall_status"], "PASSED")

    def test_run_stress_validation_bridge(self):
        mock_var_engine = MagicMock()
        expected_stress_result = {
            "portfolio_id": self.portfolio_id,
            "stress_var": round(random.uniform(5000.0, 50000.0), 2),
            "status": "STRESSED"
        }
        mock_var_engine.calculate_predictive_stress_var.return_value = expected_stress_result

        bridge = MarketPortfolioIntegrationValidationBridge(var_engine=mock_var_engine)

        result = bridge.run_stress_validation_bridge(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.port_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations
        )

        mock_var_engine.calculate_predictive_stress_var.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.port_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations
        )

        self.assertEqual(result, expected_stress_result)

    def test_stream_validation_audit_export(self):
        mock_var_engine = MagicMock()
        mock_integration_hub = MagicMock()
        expected_export = {
            "audit_id": uuid.uuid4().hex,
            "exported": True
        }
        mock_integration_hub.export_and_dispatch_stream.return_value = expected_export

        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=mock_var_engine,
            integration_hub=mock_integration_hub
        )

        result = bridge.stream_validation_audit_export(stream_data)

        mock_var_engine.process_market_stream.assert_called_once_with(stream_data)
        mock_integration_hub.export_and_dispatch_stream.assert_called_once_with(stream_data)
        self.assertEqual(result, expected_export)

    def test_run_validation_and_integration_pipeline_success(self):
        mock_var_engine = MagicMock()
        expected_var_report = {
            "portfolio_id": self.portfolio_id,
            "scenario_code": self.scenario_code,
            "var_value": round(random.uniform(10.0, 100.0), 2)
        }
        mock_var_engine.calculate_predictive_var.return_value = expected_var_report

        mock_integration_hub = MagicMock()

        bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=mock_var_engine,
            integration_hub=mock_integration_hub
        )

        result = bridge.run_validation_and_integration_pipeline(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.port_value,
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        mock_var_engine.calculate_predictive_var.assert_called_once()
        mock_integration_hub.run_integrated_pipeline.assert_called_once_with(
            self.url, self.symbol, self.shifts, self.telegram_token, self.chat_id
        )

        self.assertTrue(result["validation_status"])
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["scenario_code"], self.scenario_code)
        self.assertEqual(result["var_report"], expected_var_report)

    def test_run_validation_and_integration_pipeline_fallback(self):
        mock_var_engine = MagicMock()
        mock_var_engine.calculate_predictive_var.side_effect = Exception(uuid.uuid4().hex)

        mock_integration_hub = MagicMock()

        bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=mock_var_engine,
            integration_hub=mock_integration_hub
        )

        result = bridge.run_validation_and_integration_pipeline(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.port_value,
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        mock_integration_hub.run_integrated_pipeline.assert_called_once_with(
            self.url, self.symbol, self.shifts, self.telegram_token, self.chat_id
        )

        self.assertTrue(result["validation_status"])
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["scenario_code"], self.scenario_code)
        self.assertEqual(result["var_report"]["status"], "FALLBACK")
        self.assertEqual(result["var_report"]["var_value"], 0.0)

if __name__ == "__main__":
    unittest.main()