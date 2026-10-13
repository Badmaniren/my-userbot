import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_deep_forecaster import market_portfolio_stress_deep_forecaster
from skills.db_storage import db_storage
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_scenario_ matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_ml_feature_builder import market_portfolio_ml_feature_builder

class TestMarketPortfolioStressDeepForecasterIntegration(unittest.TestCase):

    def test_deep_forecaster_pipeline_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        historical_anomaly_threshold = round(random.uniform(1.5, 4.0), 2)
        scenario_intensity = round(random.uniform(0.1, 0.9), 2)
        
        anomaly_data = market_anomaly_detector(
            portfolio_id=portfolio_id,
            threshold=historical_anomaly_threshold
        )
        self.assertIsNotNone(anomaly_data)

        features = market_portfolio_ml_feature_builder(
            portfolio_id=portfolio_id,
            raw_data=anomaly_data
        )
        self.assertIsNotNone(features)

        simulation_matrix = market_portfolio_scenario_simulator(
            portfolio_id=portfolio_id,
            intensity=scenario_intensity
        )
        self.assertIsNotNone(simulation_matrix)

        matrix_evaluation = market_portfolio_stress_scenario_matrix_evaluator(
            scenario_matrix=simulation_matrix,
            features=features
        )
        self.assertIsNotNone(matrix_evaluation)

        forecast_result = market_portfolio_stress_deep_forecaster(
            portfolio_id=portfolio_id,
            anomaly_insights=anomaly_data,
            scenario_evaluations=matrix_evaluation
        )

        self.assertIn("forecast_id", forecast_result)
        self.assertEqual(forecast_result["portfolio_id"], portfolio_id)
        self.assertIsInstance(forecast_result["stress_probability"], float)

        stored_record = db_storage(
            action="get",
            table="deep_forecasts",
            record_id=forecast_result["forecast_id"]
        )
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)
        self.assertEqual(stored_record.get("forecast_id"), forecast_result["forecast_id"])

if __name__ == "__main__":
    unittest.main()