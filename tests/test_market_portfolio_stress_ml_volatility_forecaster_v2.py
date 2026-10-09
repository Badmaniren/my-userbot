import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    ForecasterError,
    InvalidDataError
)

class TestMarketPortfolioStressMLVolatilityForecasterV2(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.anomaly_detector = MagicMock()
        
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool,
            market_anomaly_detector=self.anomaly_detector
        )

    def test_successful_volatility_forecast(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = "".join(random.choices(string.ascii_uppercase, k=6))
        expected_volatility = round(random.uniform(0.01, 0.99), 4)

        raw_payload = f"PORTFOLIO:{portfolio_id}|SCENARIO:{scenario_code}|VAL:{random.randint(100, 1000)}"
        mock_stream = io.BytesIO(raw_payload.encode('utf-8'))

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = mock_stream
            mock_response.text = raw_payload
            mock_get.return_value = mock_response

            self.extractor_tool.extract.return_value = {
                "portfolio_id": portfolio_id,
                "scenario": scenario_code,
                "historical_vol": expected_volatility
            }

            result = self.forecaster.forecast_volatility(portfolio_id, scenario_code)

            self.assertIsInstance(result, dict)
            self.assertIn("predicted_volatility", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario_code"], scenario_code)
            self.db_storage.save_forecast.assert_called_once()

    def test_invalid_input_raises_exception(self):
        bad_portfolio_id = ""
        bad_scenario_code = "".join(random.choices(string.punctuation, k=5))

        with self.assertRaises((InvalidDataError, ValueError, TypeError)):
            self.forecaster.forecast_volatility(bad_portfolio_id, bad_scenario_code)

    def test_anomaly_detection_integration(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = "".join(random.choices(string.ascii_letters, k=8))
        
        soup_content = f"<html><body><div id='{portfolio_id}'>Anomaly Score: {random.randint(50, 100)}</div></body></html>"
        soup = BeautifulSoup(soup_content, 'html.parser')

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.BeautifulSoup', return_value=soup):
            self.anomaly_detector.analyze.return_value = {"is_anomaly": True, "severity": "CRITICAL"}

            with self.assertRaises(ForecasterError):
                self.forecaster.evaluate_stress_anomaly(portfolio_id, scenario_code, soup_content)

            self.anomaly_detector.analyze.assert_called_once()

    def test_network_failure_handling(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = str(uuid.uuid4())
        target_url = f"https://api.market-stress-{uuid.uuid4().hex}.internal/v2/forecast"

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster_v2.requests.get', side_effect=requests.exceptions.ConnectionError("Network unreachable")):
            with self.assertRaises(ForecasterError):
                self.forecaster.fetch_external_ml_metrics(target_url, portfolio_id, scenario_code)

    def test_randomized_monte_carlo_stress_matrix(self):
        iterations = random.randint(10, 50)
        base_vol = random.uniform(0.1, 0.5)
        
        matrix_data = [
            {"iter": i, "shock": random.uniform(-0.5, 0.5), "weight": random.random()} 
            for i in range(iterations)
        ]

        self.extractor_tool.process_matrix.return_value = matrix_data

        result = self.forecaster.run_monte_carlo_simulation(base_vol, matrix_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["iterations_run"], iterations)
        self.assertIn("aggregated_risk_score", result)
        self.assertGreaterEqual(result["aggregated_risk_score"], 0.0)

    def test_parser_with_garbage_binary_stream(self):
        random_bytes = bytes([random.randint(0, 255) for _ in range(128)])
        binary_stream = io.BytesIO(random_bytes)

        with self.assertRaises((ForecasterError, ValueError, UnicodeDecodeError)):
            self.forecaster.parse_stream_payload(binary_stream)

if __name__ == '__main__':
    unittest.main()