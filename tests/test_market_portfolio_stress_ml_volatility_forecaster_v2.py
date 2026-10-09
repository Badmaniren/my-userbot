import io
import unittest
import uuid
import random
import string
from unittest.mock import patch, MagicMock
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
        self.extractor_mock = MagicMock()
        self.anomaly_detector_mock = MagicMock()
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
            db_storage=self.db_storage_mock,
            extractor_tool_1790087207=self.extractor_mock,
            market_anomaly_detector=self.anomaly_detector_mock
        )

    def test_forecast_volatility_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=8))
        target_url = f"https://api.market-stress-{portfolio_id}.internal/v2/forecast"
        
        expected_historical_vol = round(random.uniform(0.1, 0.9), 4)
        self.extractor_mock.extract.return_value = {"historical_vol": expected_historical_vol}
        
        mock_response = MagicMock()
        mock_response.text = f"<html><body><span>{uuid.uuid4().hex}</span></body></html>"
        mock_response.status_code = 200

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.requests.get', return_value=mock_response) as mock_get:
            result = self.forecaster.forecast_volatility(portfolio_id, scenario_code)
            
            mock_get.assert_called_once_with(target_url)
            self.extractor_mock.extract.assert_called_once_with(mock_response.text)
            self.db_storage_mock.save_forecast.assert_called_once()
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario_code"], scenario_code)
            self.assertEqual(result["predicted_volatility"], round(expected_historical_vol * 1.25, 4))

    def test_forecast_volatility_invalid_portfolio_id(self):
        for invalid_id in [None, 12345, "", {}]:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(InvalidDataError):
                    self.forecaster.forecast_volatility(invalid_id, "VALID_SCENARIO")

    def test_forecast_volatility_invalid_scenario_code(self):
        invalid_scenarios = [None, 9876, "", "SCENARIO#1", "CODE!"]
        for invalid_scen in invalid_scenarios:
            with self.subTest(invalid_scen=invalid_scen):
                with self.assertRaises(InvalidDataError):
                    self.forecaster.forecast_volatility(uuid.uuid4().hex, invalid_scen)

    def test_forecast_volatility_http_error(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=6))
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.requests.get', return_value=mock_response):
            with self.assertRaises(requests.exceptions.HTTPError):
                self.forecaster.forecast_volatility(portfolio_id, scenario_code)

    def test_evaluate_stress_anomaly_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=5))
        soup_content = f"<html><body><div id='{portfolio_id}'>content</div></body></html>"
        
        analysis_result = {"is_anomaly": False, "severity": "NONE"}
        self.anomaly_detector_mock.analyze.return_value = analysis_result

        result = self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)
        
        self.anomaly_detector_mock.analyze.assert_called_once_with(soup_content)
        self.assertEqual(result, analysis_result)

    def test_evaluate_stress_anomaly_element_not_found(self):
        portfolio_id = uuid.uuid4().hex
        missing_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=5))
        soup_content = f"<html><body><div id='{missing_id}'>content</div></body></html>"

        with self.assertRaises(ForecasterError):
            self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)

    def test_evaluate_stress_anomaly_detected(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=5))
        soup_content = f"<html><body><div id='{portfolio_id}'>content</div></body></html>"
        
        severity_level = random.choice(["HIGH", "CRITICAL", "MODERATE"])
        analysis_result = {"is_anomaly": True, "severity": severity_level}
        self.anomaly_detector_mock.analyze.return_value = analysis_result

        with self.assertRaises(ForecasterError) as ctx:
            self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)
        
        self.assertIn(severity_level, str(ctx.exception))

    def test_fetch_external_ml_metrics_success(self):
        target_url = f"https://ml-metrics-{uuid.uuid4().hex}.internal/api"
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=5))
        expected_json = {"metric": random.random(), "status": "ok"}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_json
        mock_response.status_code = 200

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.requests.get', return_value=mock_response) as mock_get:
            result = self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)
            mock_get.assert_called_once_with(target_url)
            self.assertEqual(result, expected_json)

    def test_fetch_external_ml_metrics_network_error(self):
        target_url = f"https://ml-metrics-{uuid.uuid4().hex}.internal/api"
        portfolio_id = uuid.uuid4().hex
        scenario_code = ''.join(random.choices(string.ascii_letters, k=5))

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.requests.get', side_effect=requests.exceptions.ConnectionError("Down")):
            with self.assertRaises(ForecasterError):
                self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)

    def test_run_monte_carlo_simulation(self):
        base_volatility = round(random.uniform(0.1, 0.5), 4)
        shocks_count = random.randint(3, 10)
        matrix_data = [{"shock": round(random.uniform(-0.05, 0.05), 4)} for _ in range(shocks_count)]
        
        expected_avg_shock = sum(item["shock"] for item in matrix_data) / shocks_count
        expected_risk_score = max(0.0, base_volatility + expected_avg_shock)

        result = self.forecaster.run_monte_carlo_simulation(base_volatility, matrix_data)

        self.assertEqual(result["iterations_run"], shocks_count)
        self.assertAlmostEqual(result["aggregated_risk_score"], expected_risk_score, places=4)

    def test_parse_stream_payload(self):
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        binary_stream = io.BytesIO(random_string.encode('utf-8'))

        parsed_text = self.forecaster.parse_stream_payload(binary_stream)
        self.assertEqual(parsed_text, random_string)

    def test_forecast_portfolio_stress_volatility_function(self):
        portfolio_id = uuid.uuid4().hex
        base_vol = round(random.uniform(0.1, 0.5), 4)
        multiplier = round(random.uniform(1.0, 3.0), 2)
        confidence_level = round(random.uniform(0.9, 0.99), 2)

        scenario_data = {"multiplier": multiplier}
        monte_carlo_metrics = {"volatility_baseline": base_vol}

        result = forecast_portfolio_stress_volatility(portfolio_id, scenario_data, monte_carlo_metrics, confidence_level)

        expected_volatility = round(base_vol * multiplier * confidence_level, 4)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["confidence_level"], confidence_level)
        self.assertEqual(result["predicted_volatility"], expected_volatility)

    def test_run_scenario_simulation_function(self):
        scenario_id = uuid.uuid4().hex
        base_multiplier = round(random.uniform(1.1, 5.0), 2)

        result = run_scenario_simulation(scenario_id, base_multiplier)

        self.assertEqual(result["scenario_id"], scenario_id)
        self.assertEqual(result["multiplier"], base_multiplier)