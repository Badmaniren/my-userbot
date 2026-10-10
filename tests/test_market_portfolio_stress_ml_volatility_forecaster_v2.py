import io
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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
        self.extractor_mock = MagicMock()
        self.anomaly_detector_mock = MagicMock()
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
            db_storage=self.db_storage_mock,
            extractor_tool_1790087207=self.extractor_mock,
            market_anomaly_detector=self.anomaly_detector_mock
        )

    @unittest.skipIf(requests is None, "requests module not installed")
    def test_forecast_volatility_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        historical_vol = round(random.uniform(0.1, 0.9), 4)

        self.extractor_mock.extract.return_value = {"historical_vol": historical_vol}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = f"<html><body>{uuid.uuid4().hex}</body></html>"
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = self.forecaster.forecast_volatility(portfolio_id, scenario_code)

            mock_get.assert_called_once_with(f"https://api.market-stress-{portfolio_id}.internal/v2/forecast")
            self.extractor_mock.extract.assert_called_once_with(mock_response.text)
            self.db_storage_mock.save_forecast.assert_called_once()

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario_code"], scenario_code)
            self.assertEqual(result["predicted_volatility"], round(historical_vol * 1.25, 4))

    def test_forecast_volatility_invalid_portfolio_id(self):
        for invalid_id in [None, 12345, "", {}]:
            with self.assertRaises(InvalidDataError):
                self.forecaster.forecast_volatility(invalid_id, uuid.uuid4().hex)

    def test_forecast_volatility_invalid_scenario_code(self):
        valid_id = uuid.uuid4().hex
        invalid_codes = [None, 999, "", "scenario@code", "scenario#code", "scenario!"]
        for code in invalid_codes:
            with self.assertRaises(InvalidDataError):
                self.forecaster.forecast_volatility(valid_id, code)

    @unittest.skipIf(requests is None, "requests module not installed")
    def test_forecast_volatility_request_exception(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Down")
            mock_get.return_value = mock_response

            with self.assertRaises(requests.exceptions.HTTPError):
                self.forecaster.forecast_volatility(portfolio_id, scenario_code)

    def test_evaluate_stress_anomaly_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        soup_content = f"<html><body><div id='{portfolio_id}'>content</div></body></html>"

        self.anomaly_detector_mock.analyze.return_value = {"is_anomaly": False, "severity": "LOW"}

        result = self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)

        self.assertEqual(result, {"is_anomaly": False, "severity": "LOW"})
        self.anomaly_detector_mock.analyze.assert_called_once_with(soup_content)

    def test_evaluate_stress_anomaly_element_not_found(self):
        portfolio_id = uuid.uuid4().hex
        missing_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        soup_content = f"<html><body><div id='{missing_id}'>content</div></body></html>"

        with self.assertRaises(ForecasterError):
            self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)

    def test_evaluate_stress_anomaly_detected(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        soup_content = f"<html><body><div id='{portfolio_id}'>content</div></body></html>"
        severity = random.choice(["HIGH", "CRITICAL", "MODERATE"])

        self.anomaly_detector_mock.analyze.return_value = {"is_anomaly": True, "severity": severity}

        with self.assertRaises(ForecasterError) as ctx:
            self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)
        
        self.assertIn(severity, str(ctx.exception))

    @unittest.skipIf(requests is None, "requests module not installed")
    def test_fetch_external_ml_metrics_success(self):
        target_url = f"https://metrics.{uuid.uuid4().hex}.internal/ml"
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        expected_json = {"metric": random.uniform(0.0, 1.0), "status": "ok"}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_json
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)

            mock_get.assert_called_once_with(target_url)
            self.assertEqual(result, expected_json)

    @unittest.skipIf(requests is None, "requests module not installed")
    def test_fetch_external_ml_metrics_network_error(self):
        target_url = f"https://metrics.{uuid.uuid4().hex}.internal/ml"
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Timeout")

            with self.assertRaises(ForecasterError):
                self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)

    def test_run_monte_carlo_simulation(self):
        base_volatility = round(random.uniform(0.1, 0.5), 4)
        shocks = [round(random.uniform(-0.1, 0.2), 4) for _ in range(5)]
        matrix_data = [{"shock": s} for s in shocks]

        result = self.forecaster.run_monte_carlo_simulation(base_volatility, matrix_data)

        avg_shock = sum(shocks) / len(shocks)
        expected_risk = max(0.0, base_volatility + avg_shock)

        self.assertEqual(result["iterations_run"], len(matrix_data))
        self.assertAlmostEqual(result["aggregated_risk_score"], expected_risk, places=4)

    def test_run_monte_carlo_simulation_empty_matrix(self):
        base_volatility = round(random.uniform(0.1, 0.5), 4)
        matrix_data = []

        result = self.forecaster.run_monte_carlo_simulation(base_volatility, matrix_data)

        self.assertEqual(result["iterations_run"], 0)
        self.assertEqual(result["aggregated_risk_score"], base_volatility)

    def test_parse_stream_payload(self):
        random_text = uuid.uuid4().hex + " - " + ''.join(random.choices(string.ascii_letters, k=15))
        binary_stream = io.BytesIO(random_text.encode('utf-8'))

        parsed_string = self.forecaster.parse_stream_payload(binary_stream)

        self.assertEqual(parsed_string, random_text)

    def test_forecast_portfolio_stress_volatility_function(self):
        portfolio_id = uuid.uuid4().hex
        base_vol = round(random.uniform(0.1, 0.4), 4)
        multiplier = round(random.uniform(1.0, 2.5), 2)
        confidence_level = round(random.uniform(0.8, 0.99), 2)

        scenario_data = {"multiplier": multiplier}
        monte_carlo_metrics = {"volatility_baseline": base_vol}

        result = forecast_portfolio_stress_volatility(portfolio_id, scenario_data, monte_carlo_metrics, confidence_level)

        expected_vol = round(base_vol * multiplier * confidence_level, 4)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["predicted_volatility"], expected_vol)
        self.assertEqual(result["confidence_level"], confidence_level)

    def test_run_scenario_simulation_function(self):
        scenario_id = uuid.uuid4().hex
        base_multiplier = round(random.uniform(0.5, 3.0), 2)

        result = run_scenario_simulation(scenario_id, base_multiplier)

        self.assertEqual(result["scenario_id"], scenario_id)
        self.assertEqual(result["multiplier"], base_multiplier)

if __name__ == '__main__':
    unittest.main()