import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_ml_anomaly_predictor import market_portfolio_stress_ml_anomaly_predictor
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.db_storage import db_storage

class TestMarketPortfolioStressMlAnomalyPredictorIntegration(unittest.TestCase):
    def test_ml_anomaly_predictor_end_to_end_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        run_seed = random.randint(1000, 99999)
        historical_depth = random.randint(30, 365)

        collector_payload = {
            "portfolio_id": portfolio_id,
            "depth_days": historical_depth,
            "seed": run_seed,
            "mode": "historical_stress"
        }

        raw_data = market_portfolio_collector_agent(collector_payload)
        self.assertIsNotNone(raw_data, "Collector agent must return historical market data.")

        scenario_payload = {
            "portfolio_id": portfolio_id,
            "input_data": raw_data,
            "shock_multiplier": round(random.uniform(1.1, 3.5), 2)
        }

        scenario_results = market_portfolio_stress_scenario_pipeline(scenario_payload)
        self.assertIn("scenarios", scenario_results, "Scenario pipeline must generate stress matrices.")

        predictor_input = {
            "portfolio_id": portfolio_id,
            "stress_scenarios": scenario_results["scenarios"],
            "anomaly_threshold": round(random.uniform(0.85, 0.99), 4),
            "execution_id": str(uuid.uuid4())
        }

        prediction_output = market_portfolio_stress_ml_anomaly_predictor(predictor_input)

        self.assertIsInstance(prediction_output, dict, "Predictor must return a dictionary payload.")
        self.assertIn("anomaly_detected", prediction_output, "Output must contain anomaly detection flag.")
        self.assertIn("critical_drawdown_probability", prediction_output, "Output must calculate critical drawdown probability.")

        db_record = {
            "id": predictor_input["execution_id"],
            "portfolio_id": portfolio_id,
            "prediction": prediction_output
        }
        db_storage(db_record)

        expected_file_marker = f"anomaly_report_{portfolio_id}.json"

        self.assertTrue(
            isinstance(prediction_output.get("critical_drawdown_probability"), float),
            "Probability must be a float value derived from ML processing."
        )

if __name__ == "__main__":
    unittest.main()