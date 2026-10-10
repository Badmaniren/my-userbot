import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import logging
from skills.market_portfolio_integration_validation_bridge import MarketPortfolioIntegrationValidationBridge

logging.basicConfig(level=logging.INFO)

class TestMarketPortfolioIntegrationValidationBridge(unittest.TestCase):

    def setUp(self):
        self.var_engine_mock = MagicMock()
        self.integration_hub_mock = MagicMock()
        self.bridge = MarketPortfolioIntegrationValidationBridge(
            var_engine=self.var_engine_mock,
            integration_hub=self.integration_hub_mock
        )

    def test_run_end_to_end_validation_pipeline_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        shifts = [random.uniform(-0.1, 0.1) for _ in range(3)]
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(100000, 999999))
        simulations = random.randint(100, 1000)
        horizon_days = random.randint(1, 30)
        confidence_level = random.uniform(0.9, 0.99)
        port_value = random.uniform(10000.0, 1000000.0)
        scenario_params = {uuid.uuid4().hex: random.random()}
        iterations = random.randint(5, 50)

        expected_var_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_integration_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.var_engine_mock.calculate_predictive_var.return_value = expected_var_report
        self.integration_hub_mock.run_integrated_pipeline.return_value = expected_integration_report

        result = self.bridge.run_end_to_end_validation_pipeline(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            url=url,
            symbol=symbol,
            shifts=shifts,
            telegram_token=telegram_token,
            chat_id=chat_id,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            port_value=port_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("validation_id", result)
        self.assertEqual(result["var_report"], expected_var_report)
        self.assertEqual(result["integration_report"], expected_integration_report)
        self.assertEqual(result["overall_status"], "PASSED")

        self.var_engine_mock.calculate_predictive_var.assert_called_once_with(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            portfolio_value=port_value,
            scenario_params=scenario_params,
            iterations=iterations
        )
        self.integration_hub_mock.run_integrated_pipeline.assert_called_once_with(
            url, symbol, shifts, telegram_token, chat_id
        )

    def test_run_stress_validation_bridge(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = random.uniform(50000.0, 500000.0)
        scenario_params = {uuid.uuid4().hex: random.uniform(1.0, 5.0)}
        confidence_level = random.uniform(0.95, 0.99)
        horizon_days = random.randint(5, 60)
        iterations = random.randint(10, 100)

        expected_stress_result = {uuid.uuid4().hex: random.random()}
        self.var_engine_mock.calculate_predictive_stress_var.return_value = expected_stress_result

        result = self.bridge.run_stress_validation_bridge(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

        self.assertEqual(result, expected_stress_result)
        self.var_engine_mock.calculate_predictive_stress_var.assert_called_once_with(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

    def test_stream_validation_audit_export(self):
        stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_export_result = {uuid.uuid4().hex: random.randint(1, 100)}
        self.integration_hub_mock.export_and_dispatch_stream.return_value = expected_export_result

        result = self.bridge.stream_validation_audit_export(stream_data)

        self.assertEqual(result, expected_export_result)
        self.var_engine_mock.process_market_stream.assert_called_once_with(stream_data)
        self.integration_hub_mock.export_and_dispatch_stream.assert_called_once_with(stream_data)

    def test_run_validation_and_integration_pipeline_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        simulations = random.randint(50, 500)
        horizon_days = random.randint(1, 14)
        confidence_level = random.uniform(0.9, 0.99)
        portfolio_value = random.uniform(1000.0, 100000.0)
        url = f"https://{uuid.uuid4().hex}.org"
        symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        shifts = [random.random() for _ in range(2)]
        telegram_token = uuid.uuid4().hex
        chat_id = uuid.uuid4().hex

        expected_var_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.var_engine_mock.calculate_predictive_var.return_value = expected_var_report

        result = self.bridge.run_validation_and_integration_pipeline(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            portfolio_value=portfolio_value,
            url=url,
            symbol=symbol,
            shifts=shifts,
            telegram_token=telegram_token,
            chat_id=chat_id
        )

        self.assertTrue(result["validation_status"])
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["scenario_code"], scenario_code)
        self.assertEqual(result["var_report"], expected_var_report)

        self.integration_hub_mock.run_integrated_pipeline.assert_called_once_with(
            url, symbol, shifts, telegram_token, chat_id
        )

    def test_run_validation_and_integration_pipeline_raises_exception(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        simulations = random.randint(50, 500)
        horizon_days = random.randint(1, 14)
        confidence_level = random.uniform(0.9, 0.99)
        portfolio_value = random.uniform(1000.0, 100000.0)
        url = f"https://{uuid.uuid4().hex}.org"
        symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        shifts = [random.random() for _ in range(2)]
        telegram_token = uuid.uuid4().hex
        chat_id = uuid.uuid4().hex

        error_message = uuid.uuid4().hex
        self.var_engine_mock.calculate_predictive_var.side_effect = RuntimeError(error_message)

        with self.assertRaises(RuntimeError) as context:
            self.bridge.run_validation_and_integration_pipeline(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                url=url,
                symbol=symbol,
                shifts=shifts,
                telegram_token=telegram_token,
                chat_id=chat_id
            )

        self.assertIn(error_message, str(context.exception))
        self.integration_hub_mock.run_integrated_pipeline.assert_not_called()

    def test_init_defaults_creation(self):
        db_path = f"{uuid.uuid4().hex}.sqlite"
        bridge_default = MarketPortfolioIntegrationValidationBridge(db_storage=db_path)
        self.assertIsNotNone(bridge_default.var_engine)
        self.assertIsNotNone(bridge_default.integration_hub)

if __name__ == '__main__':
    unittest.main()