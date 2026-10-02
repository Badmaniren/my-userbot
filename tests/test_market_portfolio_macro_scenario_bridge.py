import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.market_portfolio_macro_scenario_bridge import (
    MacroBridgeException,
    MarketPortfolioMacroScenarioBridgeException,
    MacroScenarioBridge,
    MarketPortfolioMacroScenarioBridgeModule,
    market_portfolio_macro_scenario_bridge
)


class TestMarketPortfolioMacroScenarioBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.scenario_id = uuid.uuid4().hex
        self.macro_factor_id = uuid.uuid4().hex
        self.output_destination = f"/tmp/{uuid.uuid4().hex}.txt"

        self.mock_db = MagicMock()
        self.mock_pipeline = MagicMock()
        self.mock_gateway = MagicMock()

        self.bridge = MacroScenarioBridge(
            db_storage=self.mock_db,
            market_portfolio_stress_scenario_pipeline=self.mock_pipeline,
            market_portfolio_api_gateway=self.mock_gateway
        )

    def test_evaluate_macro_scenario_anomaly_true(self):
        random_shock = random.uniform(-10.0, 10.0)
        indicators = {"anomaly_flag": True, "gdp_shock": random_shock}
        self.mock_gateway.fetch_macro_indicators.return_value = indicators

        expected_result = {"status": uuid.uuid4().hex, "shock": random_shock}
        self.mock_pipeline.run_stress_test.return_value = expected_result

        result = self.bridge.evaluate_macro_scenario(self.portfolio_id)

        self.mock_gateway.fetch_macro_indicators.assert_called_once()
        self.mock_pipeline.run_stress_test.assert_called_once_with(self.portfolio_id, indicators)
        self.mock_db.log_anomaly.assert_called_once_with(expected_result)
        self.mock_db.save_macro_event.assert_not_called()
        self.assertEqual(result, expected_result)

    def test_evaluate_macro_scenario_anomaly_false(self):
        random_shock = random.uniform(-5.0, 5.0)
        indicators = {"anomaly_flag": False, "gdp_shock": random_shock}
        self.mock_gateway.fetch_macro_indicators.return_value = indicators

        expected_result = {"status": uuid.uuid4().hex, "shock": random_shock}
        self.mock_pipeline.run_stress_test.return_value = expected_result

        result = self.bridge.evaluate_macro_scenario(self.portfolio_id)

        self.mock_gateway.fetch_macro_indicators.assert_called_once()
        self.mock_pipeline.run_stress_test.assert_called_once_with(self.portfolio_id, indicators)
        self.mock_db.save_macro_event.assert_called_once_with(expected_result)
        self.mock_db.log_anomaly.assert_not_called()
        self.assertEqual(result, expected_result)

    def test_evaluate_macro_scenario_request_exception(self):
        err_msg = uuid.uuid4().hex
        self.mock_gateway.fetch_macro_indicators.side_effect = requests.RequestException(err_msg)

        with self.assertRaises(MacroBridgeException) as ctx:
            self.bridge.evaluate_macro_scenario(self.portfolio_id)

        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.market_portfolio_macro_scenario_bridge.requests.get")
    def test_stream_external_macro_feed_success(self, mock_get):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = io.BytesIO(random_bytes)
        mock_get.return_value = mock_response

        raw_stream = self.bridge.stream_external_macro_feed(self.portfolio_id)
        self.assertEqual(raw_stream.read(), random_bytes)
        mock_get.assert_called_once_with("http://example.com/macro-stream")

    @patch("skills.market_portfolio_macro_scenario_bridge.requests.get")
    def test_stream_external_macro_feed_bad_status(self, mock_get):
        bad_status = random.choice([400, 404, 500, 503])
        mock_response = MagicMock()
        mock_response.status_code = bad_status
        mock_get.return_value = mock_response

        with self.assertRaises(MacroBridgeException) as ctx:
            self.bridge.stream_external_macro_feed(self.portfolio_id)

        self.assertIn(str(bad_status), str(ctx.exception))

    def test_module_execute_multi_factor_forecast_success(self):
        module_instance = MarketPortfolioMacroScenarioBridgeModule()
        mock_db_inner = MagicMock()
        module_instance.db = mock_db_inner

        random_shock_val = random.uniform(1.0, 100.0)
        mock_db_inner.get_macro_scenario_forecast.return_value = {
            "applied_gdp_shock": random_shock_val
        }

        payload = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.scenario_id,
            "macro_factor_id": self.macro_factor_id,
            "output_destination": self.output_destination
        }

        result = module_instance.execute_multi_factor_forecast(payload)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["scenario_id"], self.scenario_id)
        self.assertEqual(result["macro_factor_id"], self.macro_factor_id)
        self.assertEqual(result["applied_gdp_shock"], random_shock_val)
        self.assertIn("forecast_id", result)

        mock_db_inner.get_macro_scenario_forecast.assert_called_once_with(self.macro_factor_id)
        mock_db_inner.save_macro_scenario_forecast.assert_called_once_with(result)

    def test_module_execute_multi_factor_forecast_invalid_payload(self):
        module_instance = MarketPortfolioMacroScenarioBridgeModule()

        incomplete_payloads = [
            {"scenario_id": self.scenario_id, "macro_factor_id": self.macro_factor_id},
            {"portfolio_id": self.portfolio_id, "macro_factor_id": self.macro_factor_id},
            {"portfolio_id": self.portfolio_id, "scenario_id": self.scenario_id},
            {}
        ]

        for payload in incomplete_payloads:
            with self.assertRaises(MarketPortfolioMacroScenarioBridgeException):
                module_instance.execute_multi_factor_forecast(payload)

    def test_module_execute_multi_factor_forecast_factor_not_found(self):
        module_instance = MarketPortfolioMacroScenarioBridgeModule()
        mock_db_inner = MagicMock()
        module_instance.db = mock_db_inner

        mock_db_inner.get_macro_scenario_forecast.return_value = None

        payload = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.scenario_id,
            "macro_factor_id": self.macro_factor_id
        }

        with self.assertRaises(MarketPortfolioMacroScenarioBridgeException) as ctx:
            module_instance.execute_multi_factor_forecast(payload)

        self.assertIn("Macro factor not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()