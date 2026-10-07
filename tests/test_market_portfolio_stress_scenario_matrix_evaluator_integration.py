import unittest
import uuid
import random
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class RealDbStorageStub:
    def __init__(self, random_seed_val):
        self.seed_val = random_seed_val

    def fetch_history(self, portfolio_id: str, historical_window: int):
        return [{"value": float(self.seed_val + i * 10)} for i in range(historical_window)]

    def fetch_stream(self, portfolio_id: str):
        class StreamStub:
            def __init__(self, text):
                self.text = text
            def read(self):
                return self.text.encode('utf-8')
        return StreamStub(f"<html><body>Stream data for {portfolio_id} - {self.seed_val}</body></html>")

class RealExtractorToolStub:
    def __init__(self, anomaly_val):
        self.anomaly_val = anomaly_val

    def analyze(self, scenario_token: str):
        return {"scenario_token": scenario_token, "anomaly_metric": self.anomaly_val}

class TestMarketPortfolioStressScenarioMatrixEvaluatorIntegration(unittest.TestCase):
    def test_end_to_end_matrix_evaluation_pipeline(self):
        random_seed_val = random.randint(100, 9999)
        portfolio_id = str(uuid.uuid4())
        evaluation_id = str(uuid.uuid4())
        historical_window = random.randint(3, 10)
        anomaly_threshold = float(random.randint(40, 80))
        actual_anomaly_metric = anomaly_threshold + float(random.randint(1, 20))
        scenario_token = str(uuid.uuid4())
        monte_carlo_score = round(random.uniform(0.1, 0.9), 4)

        db_storage = RealDbStorageStub(random_seed_val)
        extractor_1 = RealExtractorToolStub(actual_anomaly_metric)
        extractor_2 = RealExtractorToolStub(0.0)

        evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor_1,
            extractor_tool_1790102839=extractor_2
        )

        matrix_result = evaluator.evaluate_matrix(portfolio_id, historical_window)
        self.assertEqual(matrix_result["portfolio_id"], portfolio_id)
        self.assertIn("evaluation_score", matrix_result)
        self.assertIsInstance(matrix_result["evaluation_score"], float)

        stream_result = evaluator.evaluate_stream_matrix(portfolio_id, None)
        self.assertEqual(stream_result["portfolio_id"], portfolio_id)
        self.assertTrue(stream_result["fallback_triggered"])

        anomaly_detected = evaluator.detect_matrix_anomalies(scenario_token, anomaly_threshold)
        self.assertTrue(anomaly_detected)

        evaluation_payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {
                "score": monte_carlo_score
            }
        }

        pipeline_result = evaluate_stress_scenario_matrix(evaluation_payload)
        
        self.assertEqual(pipeline_result["evaluation_id"], evaluation_id)
        self.assertEqual(pipeline_result["portfolio_id"], portfolio_id)
        expected_matrix_score = round(monte_carlo_score * 1.1, 4)
        self.assertEqual(pipeline_result["matrix_score"], expected_matrix_score)

if __name__ == "__main__":
    unittest.main()