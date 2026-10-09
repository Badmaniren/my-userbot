import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    ForecasterError,
    InvalidDataError,
    MarketPortfolioStressMLVolatilityForecasterV2,
    forecast_portfolio_stress_volatility,
    run_scenario_simulation
)

class TestMarketPortfolioStressMLVolatilityForecasterV2(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.extractor_tool_mock = MagicMock()
        self.anomaly_detector_mock = MagicMock()
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
            db_storage=self.db_storage_mock,
            extractor_tool_1790087207=self.extractor_tool_mock,
            market_anomaly_detector=self.anomaly_detector_mock
        )

    def test_forecast_volatility_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = "".join(random.choices(string.ascii_letters, k=8))
        historical_vol = round(random.uniform(0.1, 0.9), 4)

        self.extractor_tool_mock.extract.return_value = {"historical_vol": historical_vol}

        mock_response = MagicMock()
        mock_response.text = f"<div>{uuid.uuid4().hex}</div>"
        mock_response.status_code = 200

        with patch("requests.get", return_value=mock_response) as get_patch:
            result = self.forecaster.forecast_volatility(portfolio_id, scenario_code)
            get_patch.assert_called_once_with(f"https://api.market-stress-{portfolio_id}.internal/v2/forecast")

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["scenario_code"], scenario_code)
        self.assertEqual(result["predicted_volatility"], round(historical_vol * 1.25, 4))
        self.db_storage_mock.save_forecast.assert_called_once_with(result)

    def test_forecast_volatility_invalid_portfolio_id(self):
        for invalid_id in [None, "", 12345]:
            with self.assertRaises(InvalidDataError):
                self.forecaster.forecast_volatility(invalid_id, "SCENARIO_A")

    def test_forecast_volatility_invalid_scenario_code(self):
        portfolio_id = uuid.uuid4().hex
        for invalid_code in [None, "", 999, "SCENARIO#CODE"]:
            with self.assertRaises(InvalidDataError):
                self.forecaster.forecast_volatility(portfolio_id, invalid_code)

    def test_forecast_volatility_request_error(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = "".join(random.choices(string.ascii_letters, k=6))

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")

        with patch("requests.get", return_value=mock_response):
            with self.assertRaises(requests.exceptions.HTTPError):
                self.forecaster.forecast_volatility(portfolio_id, scenario_code)

    def test_evaluate_stress_anomaly_success(self):
        portfolio_id = uuid.uuid4().hex
        soup_content = f"<html><body><div id='{portfolio_id}'>content</div></body></html>"
        self.anomaly_detector_mock.analyze.return_value = {"is_anomaly": False}

        result = self.forecaster.evaluate_stress_anomaly(portfolio_id, "CODE", soup_content)
        self.assertEqual(result, {"is_anomaly": False})

    def test_evaluate_stress_anomaly_element_not_found(self):
        portfolio_id = uuid.uuid4().hex
        missing_id = uuid.uuid4().hex
        soup_content = f"<html><body><div id='{missing_id}'>content</div></body></html>"

        with self.assertRaises(ForecasterError):
            self.forecaster.evaluate_stress_anomaly(portfolio_id, "CODE", soup_content)

    def test_evaluate_stress_anomaly_detected(self):
        portfolio_id = uuid.uuid4().hex
        soup_content = f"<html><body><div id='{portfolio_id}'>content</div></body></html>"
        severity = random.choice(["HIGH", "CRITICAL", "MODERATE"])
        self.anomaly_detector_mock.analyze.return_value = {"is_anomaly": True, "severity": severity}

        with self.assertRaises(ForecasterError) as ctx:
            self.forecaster.evaluate_stress_anomaly(portfolio_id, "CODE", soup_content)
        self.assertIn(severity, str(ctx.exception))

    def test_fetch_external_ml_metrics_success(self):
        target_url = f"https://{uuid.uuid4().hex}.internal/metrics"
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        expected_json = {"metric": random.uniform(0, 100)}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_json
        mock_response.status_code = 200

        with patch("requests.get", return_value=mock_response) as get_patch:
            result = self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)
            get_patch.assert_called_once_with(target_url)

        self.assertEqual(result, expected_json)

    def test_fetch_external_ml_metrics_network_error(self):
        target_url = f"https://{uuid.uuid4().hex}.internal/metrics"
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex

        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Refused")):
            with self.assertRaises(ForecasterError):
                self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)

    def test_run_monte_carlo_simulation(self):
        base_vol = round(random.uniform(0.05, 0.5), 4)
        matrix_data = [
            {"shock": round(random.uniform(-0.1, 0.2), 4)},
            {"shock": round(random.uniform(-0.1, 0.2), 4)},
            {"shock": round(random.uniform(-0.1, 0.2), 4)}
        ]

        result = self.forecaster.run_monte_carlo_simulation(base_vol, matrix_data)
        self.assertEqual(result["iterations_run"], 3)
        self.assertIsInstance(result["aggregated_risk_score"], float)

    def test_parse_stream_payload(self):
        random_text = uuid.uuid4().hex
        stream = io.BytesIO(random_text.encode('utf-8'))

        parsed = self.forecaster.parse_stream_payload(stream)
        self.assertEqual(parsed, random_text)

    def test_forecast_portfolio_stress_volatility_function(self):
        portfolio_id = uuid.uuid4().hex
        base_vol = round(random.uniform(0.1, 0.4), 4)
        multiplier = round(random.uniform(1.0, 2.0), 2)
        confidence_level = round(random.uniform(0.9, 0.99), 2)

        scenario_data = {"multiplier": multiplier}
        monte_carlo_metrics = {"volatility_baseline": base_vol}

        res = forecast_portfolio_stress_volatility(portfolio_id, scenario_data, monte_carlo_metrics, confidence_level)

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["confidence_level"], confidence_level)
        expected_vol = round(base_vol * multiplier * confidence_level, 4)
        self.assertEqual(res["predicted_volatility"], expected_vol)

    def test_run_scenario_simulation_function(self):
        scenario_id = uuid.uuid4().hex
        base_multiplier = round(random.uniform(1.0, 5.0), 2)

        res = run_scenario_simulation(scenario_id, base_multiplier)
        self.assertEqual(res["scenario_id"], scenario_id)
        self.assertEqual(res["multiplier"], base_multiplier)

if __name__ == '__main__':
    unittest.main()