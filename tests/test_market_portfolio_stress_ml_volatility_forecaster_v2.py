import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    ForecasterError,
    InvalidDataError,
    forecast_portfolio_stress_volatility,
    run_scenario_simulation
)

class TestMarketPortfolioStressMLVolatilityForecasterV2(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.scenario_code = "".join(random.choices(string.ascii_lowercase, k=8))
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.anomaly_detector = MagicMock()
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool,
            market_anomaly_detector=self.anomaly_detector
        )

    def test_forecast_volatility_success(self):
        historical_vol = round(random.uniform(0.1, 0.9), 4)
        self.extractor_tool.extract.return_value = {"historical_vol": historical_vol}
        
        mock_response = MagicMock()
        mock_response.text = f"<html><body><div id='{self.portfolio_id}'></div></body></html>"
        mock_response.raise_for_status.return_value = None

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.forecaster.forecast_volatility(self.portfolio_id, self.scenario_code)
            
            mock_get.assert_called_once_with(f"https://api.market-stress-{self.portfolio_id}.internal/v2/forecast")
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["scenario_code"], self.scenario_code)
            self.assertEqual(result["predicted_volatility"], round(historical_vol * 1.25, 4))
            self.db_storage.save_forecast.assert_called_once_with(result)

    def test_forecast_volatility_invalid_portfolio_id_empty(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility("", self.scenario_code)

    def test_forecast_volatility_invalid_portfolio_id_type(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility(None, self.scenario_code)

    def test_forecast_volatility_invalid_scenario_code_empty(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility(self.portfolio_id, "")

    def test_forecast_volatility_invalid_scenario_code_symbols(self):
        invalid_scenario = self.scenario_code + "#"
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility(self.portfolio_id, invalid_scenario)

    def test_evaluate_stress_anomaly_success(self):
        soup_content = f"<div><div id='{self.portfolio_id}'>Content</div></div>"
        self.anomaly_detector.analyze.return_value = {"is_anomaly": False}

        result = self.forecaster.evaluate_stress_anomaly(self.portfolio_id, self.scenario_code, soup_content)
        self.assertEqual(result, {"is_anomaly": False})

    def test_evaluate_stress_anomaly_element_not_found(self):
        soup_content = "<div><div id='wrong_id'>Content</div></div>"
        with self.assertRaises(ForecasterError):
            self.forecaster.evaluate_stress_anomaly(self.portfolio_id, self.scenario_code, soup_content)

    def test_evaluate_stress_anomaly_detected(self):
        soup_content = f"<div><div id='{self.portfolio_id}'>Content</div></div>"
        severity = uuid.uuid4().hex
        self.anomaly_detector.analyze.return_value = {"is_anomaly": True, "severity": severity}

        with self.assertRaises(ForecasterError) as ctx:
            self.forecaster.evaluate_stress_anomaly(self.portfolio_id, self.scenario_code, soup_content)
        self.assertIn(severity, str(ctx.exception))

    def test_fetch_external_ml_metrics_success(self):
        target_url = f"https://{uuid.uuid4().hex}.internal/api/metrics"
        expected_json = {"metric": random.random()}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_json
        mock_response.raise_for_status.return_value = None

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.forecaster.fetch_external_ml_metrics(target_url, self.portfolio_id, self.scenario_code)
            mock_get.assert_called_once_with(target_url)
            self.assertEqual(result, expected_json)

    def test_fetch_external_ml_metrics_network_error(self):
        target_url = f"https://{uuid.uuid4().hex}.internal/api/metrics"

        with patch('requests.get', side_effect=Exception("Network failure")):
            with self.assertRaises(ForecasterError):
                self.forecaster.fetch_external_ml_metrics(target_url, self.portfolio_id, self.scenario_code)

    def test_run_monte_carlo_simulation_valid(self):
        base_vol = round(random.uniform(0.1, 0.5), 4)
        shocks = [round(random.uniform(-0.05, 0.05), 4) for _ in range(5)]
        matrix_data = [{"shock": s} for s in shocks]

        result = self.forecaster.run_monte_carlo_simulation(base_vol, matrix_data)
        self.assertEqual(result["iterations_run"], 5)
        expected_risk = max(0.0, base_vol + (sum(shocks) / 5))
        self.assertEqual(result["aggregated_risk_score"], expected_risk)

    def test_run_monte_carlo_simulation_empty_matrix(self):
        base_vol = round(random.uniform(0.1, 0.5), 4)
        matrix_data = []

        result = self.forecaster.run_monte_carlo_simulation(base_vol, matrix_data)
        self.assertEqual(result["iterations_run"], 0)
        self.assertEqual(result["aggregated_risk_score"], base_vol)

    def test_parse_stream_payload(self):
        random_text = uuid.uuid4().hex
        binary_stream = io.BytesIO(random_text.encode('utf-8'))

        parsed = self.forecaster.parse_stream_payload(binary_stream)
        self.assertEqual(parsed, random_text)

    def test_forecast_portfolio_stress_volatility_global(self):
        base_vol = round(random.uniform(0.1, 0.4), 4)
        multiplier = round(random.uniform(1.0, 2.0), 4)
        confidence_level = round(random.uniform(0.9, 0.99), 4)

        scenario_data = {"multiplier": multiplier}
        monte_carlo_metrics = {"volatility_baseline": base_vol}

        result = forecast_portfolio_stress_volatility(
            self.portfolio_id, scenario_data, monte_carlo_metrics, confidence_level
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["confidence_level"], confidence_level)
        expected_vol = round(base_vol * multiplier * confidence_level, 4)
        self.assertEqual(result["predicted_volatility"], expected_vol)

    def test_run_scenario_simulation_global(self):
        base_multiplier = round(random.uniform(0.5, 3.0), 4)
        result = run_scenario_simulation(self.scenario_code, base_multiplier)

        self.assertEqual(result["scenario_id"], self.scenario_code)
        self.assertEqual(result["multiplier"], base_multiplier)