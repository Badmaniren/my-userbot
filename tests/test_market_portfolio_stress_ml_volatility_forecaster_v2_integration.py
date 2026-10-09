import unittest
import uuid
import random
import io
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    ForecasterError,
    InvalidDataError,
    forecast_portfolio_stress_volatility,
    run_scenario_simulation
)

class TestMarketPortfolioStressMLVolatilityForecasterV2Integration(unittest.TestCase):
    def setUp(self):
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2()
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = f"scen_{random.randint(1000, 9999)}"

    def test_invalid_portfolio_id_raises_error(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility("", self.scenario_code)

    def test_invalid_scenario_code_raises_error(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility(self.portfolio_id, "invalid@code!")

    def test_evaluate_stress_anomaly_missing_element(self):
        html_content = "<div><span>No matching ID here</span></div>"
        with self.assertRaises(ForecasterError):
            self.forecaster.evaluate_stress_anomaly(self.portfolio_id, self.scenario_code, html_content)

    def test_run_monte_carlo_simulation_calculates_correctly(self):
        base_vol = round(random.uniform(0.1, 0.5), 4)
        matrix = [{"shock": round(random.uniform(-0.1, 0.1), 4)} for _ in range(5)]
        result = self.forecaster.run_monte_carlo_simulation(base_vol, matrix)
        self.assertEqual(result["iterations_run"], 5)
        self.assertIn("aggregated_risk_score", result)
        self.assertGreaterEqual(result["aggregated_risk_score"], 0.0)

    def test_parse_stream_payload(self):
        random_text = f"stream_data_{uuid.uuid4()}"
        stream = io.BytesIO(random_text.encode('utf-8'))
        parsed = self.forecaster.parse_stream_payload(stream)
        self.assertEqual(parsed, random_text)

    def test_standalone_functions_integration(self):
        scenario_id = f"sim_{random.randint(100, 999)}"
        multiplier = round(random.uniform(1.0, 3.0), 2)
        scenario_data = run_scenario_simulation(scenario_id, multiplier)
        
        self.assertEqual(scenario_data["scenario_id"], scenario_id)
        self.assertEqual(scenario_data["multiplier"], multiplier)

        monte_carlo_metrics = {"volatility_baseline": 0.25}
        confidence = 0.95
        
        forecast_res = forecast_portfolio_stress_volatility(
            self.portfolio_id, 
            scenario_data, 
            monte_carlo_metrics, 
            confidence
        )
        
        self.assertEqual(forecast_res["portfolio_id"], self.portfolio_id)
        self.assertEqual(forecast_res["confidence_level"], confidence)
        self.assertIn("predicted_volatility", forecast_res)

if __name__ == "__main__":
    unittest.main()