import unittest
import uuid
import random
import io

from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    forecast_portfolio_stress_volatility,
    run_scenario_simulation,
    InvalidDataError,
    ForecasterError
)

class RealDatabaseStorageStub:
    def __init__(self):
        self.saved_records = []

    def save_forecast(self, result: dict):
        self.saved_records.append(result)

class RealExtractorStub:
    def extract(self, text: str) -> dict:
        return {"historical_vol": 0.3}

class RealAnomalyDetectorStub:
    def analyze(self, content: str) -> dict:
        return {"is_anomaly": False, "severity": "LOW"}

class TestMarketPortfolioStressMLVolatilityForecasterV2Integration(unittest.TestCase):
    def setUp(self):
        self.db = RealDatabaseStorageStub()
        self.extractor = RealExtractorStub()
        self.detector = RealAnomalyDetectorStub()
        
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
            db_storage=self.db,
            extractor_tool_1790087207=self.extractor,
            market_anomaly_detector=self.detector
        )

    def test_forecast_volatility_end_to_end_integration(self):
        rand_portfolio_id = f"port-{uuid.uuid4()}"
        rand_scenario_code = f"scen-{random.randint(1000, 9999)}"

        simulated_matrix = [
            {"shock": round(random.uniform(0.01, 0.05), 4)},
            {"shock": round(random.uniform(0.02, 0.08), 4)}
        ]

        scenario_res = run_scenario_simulation(
            scenario_id=rand_scenario_code,
            base_multiplier=round(random.uniform(1.1, 2.0), 2)
        )

        monte_carlo_res = self.forecaster.run_monte_carlo_simulation(
            base_volatility=0.25,
            matrix_data=simulated_matrix
        )

        confidence = round(random.uniform(0.9, 0.99), 2)
        portfolio_stress_res = forecast_portfolio_stress_volatility(
            portfolio_id=rand_portfolio_id,
            scenario_data=scenario_res,
            monte_carlo_metrics={"volatility_baseline": monte_carlo_res["aggregated_risk_score"]},
            confidence_level=confidence
        )

        self.assertEqual(portfolio_stress_res["portfolio_id"], rand_portfolio_id)
        self.assertIn("predicted_volatility", portfolio_stress_res)
        self.assertGreater(portfolio_stress_res["predicted_volatility"], 0.0)

        stream_data = io.BytesIO(f"Stream-Payload-{uuid.uuid4()}".encode('utf-8'))
        parsed_stream = self.forecaster.parse_stream_payload(stream_data)
        self.assertIn("Stream-Payload", parsed_stream)

        soup_html = f'<div><span id="{rand_portfolio_id}">Stable Data</span></div>'
        anomaly_eval = self.forecaster.evaluate_stress_anomaly(
            portfolio_id=rand_portfolio_id,
            scenario_code=rand_scenario_code,
            soup_content=soup_html
        )
        self.assertIsInstance(anomaly_eval, dict)
        self.assertFalse(anomaly_eval.get("is_anomaly", True))

    def test_invalid_data_handling(self):
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility("", "valid_scenario")

        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility("valid_portfolio", "bad_scenario!@#")

    def test_anomaly_detection_exception(self):
        class AnomalyTrueDetectorStub:
            def analyze(self, content: str) -> dict:
                return {"is_anomaly": True, "severity": "CRITICAL"}

        forecaster_anomaly = MarketPortfolioStressMLVolatilityForecasterV2(
            market_anomaly_detector=AnomalyTrueDetectorStub()
        )
        rand_id = f"port-{uuid.uuid4()}"
        soup_html = f'<div><span id="{rand_id}">Danger</span></div>'

        with self.assertRaises(ForecasterError):
            forecaster_anomaly.evaluate_stress_anomaly(
                portfolio_id=rand_id,
                scenario_code="normal_scenario",
                soup_content=soup_html
            )

if __name__ == '__main__':
    unittest.main()