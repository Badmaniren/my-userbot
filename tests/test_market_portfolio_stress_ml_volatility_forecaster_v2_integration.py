import unittest
import uuid
import random
import io
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    InvalidDataError,
    ForecasterError,
    forecast_portfolio_stress_volatility,
    run_scenario_simulation
)

class TestMarketPortfolioStressMLVolatilityForecasterV2Integration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2()

    def test_invalid_portfolio_id_raises_error(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility("", self.scenario_code)

    def test_invalid_scenario_code_raises_error(self):
        invalid_scenario = f"scen-{uuid.uuid4()}!"
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility(self.portfolio_id, invalid_scenario)

    def test_run_monte_carlo_simulation_integration(self):
        base_vol = round(random.uniform(0.1, 0.5), 4)
        matrix_data = [
            {"shock": round(random.uniform(-0.1, 0.1), 4)}
            for _ in range(random.randint(1, 5))
        ]
        result = self.forecaster.run_monte_carlo_simulation(base_vol, matrix_data)
        self.assertIn("iterations_run", result)
        self.assertIn("aggregated_risk_score", result)
        self.assertEqual(result["iterations_run"], len(matrix_data))
        self.assertGreaterEqual(result["aggregated_risk_score"], 0.0)

    def test_parse_stream_payload_integration(self):
        random_text = f"payload-{uuid.uuid4()}"
        stream = io.BytesIO(random_text.encode('utf-8'))
        parsed = self.forecaster.parse_stream_payload(stream)
        self.assertEqual(parsed, random_text)

    def test_forecast_portfolio_stress_volatility_helper(self):
        base_vol = round(random.uniform(0.1, 0.3), 4)
        multiplier = round(random.uniform(1.0, 2.0), 2)
        confidence = round(random.uniform(0.9, 0.99), 2)
        
        scenario_data = {"multiplier": multiplier}
        monte_carlo_metrics = {"volatility_baseline": base_vol}

        res = forecast_portfolio_stress_volatility(
            self.portfolio_id, 
            scenario_data, 
            monte_carlo_metrics, 
            confidence
        )

        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["confidence_level"], confidence)
        expected_vol = round(base_vol * multiplier * confidence, 4)
        self.assertEqual(res["predicted_volatility"], expected_vol)

    def test_run_scenario_simulation_compatibility(self):
        sim_id = f"sim-{uuid.uuid4().hex[:6]}"
        mult = round(random.uniform(1.1, 2.5), 2)
        sim_res = run_scenario_simulation(sim_id, mult)
        self.assertEqual(sim_res["scenario_id"], sim_id)
        self.assertEqual(sim_res["multiplier"], mult)

    def test_evaluate_stress_anomaly_missing_element(self):
        html_content = f"<div><span>No target here</span></div>"
        with self.assertRaises(ForecasterError):
            self.forecaster.evaluate_stress_anomaly(self.portfolio_id, self.scenario_code, html_content)

if __name__ == "__main__":
    unittest.main()