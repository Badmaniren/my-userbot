import unittest
import uuid
import random
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class RealDummyDbStorage:
    def __init__(self, history_data, stream_data):
        self.history_data = history_data
        self.stream_data = stream_data

    def fetch_history(self, portfolio_id: str, historical_window: int):
        return self.history_data

    def fetch_stream(self, portfolio_id: str):
        return self.stream_data

class RealDummyExtractorTool:
    def __init__(self, anomaly_metric: float):
        self.anomaly_metric = anomaly_metric

    def analyze(self, scenario_token: str):
        return {"anomaly_metric": self.anomaly_metric}

class TestMarketPortfolioStressScenarioMatrixEvaluatorIntegration(unittest.TestCase):
    def test_integration_evaluate_matrix_and_function(self):
        portfolio_id = str(uuid.uuid4())
        evaluation_id = str(uuid.uuid4())
        random_value = random.uniform(100.0, 5000.0)
        historical_window = random.randint(1, 30)

        history_data = [{"value": random_value}]
        stream_data = type('Stream', (), {'read': lambda self: b'<html><body>Test Matrix Stream</body></html>'})()

        db_storage = RealDummyDbStorage(history_data, stream_data)
        extractor_1 = RealDummyExtractorTool(0.5)
        extractor_2 = RealDummyExtractorTool(0.1)

        evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor_1,
            extractor_tool_1790102839=extractor_2
        )

        matrix_result = evaluator.evaluate_matrix(portfolio_id, historical_window)
        self.assertIn("portfolio_id", matrix_result)
        self.assertEqual(matrix_result["portfolio_id"], portfolio_id)
        self.assertIn("evaluation_score", matrix_result)
        self.assertIsInstance(matrix_result["evaluation_score"], float)

        stream_result = evaluator.evaluate_stream_matrix(portfolio_id, None)
        self.assertEqual(stream_result["portfolio_id"], portfolio_id)
        self.assertTrue(stream_result.get("fallback_triggered"))

        anomaly_detected = evaluator.detect_matrix_anomalies(str(uuid.uuid4()), 0.3)
        self.assertTrue(anomaly_detected)

        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {
                "score": round(random.uniform(0.1, 0.9), 4)
            }
        }
        func_result = evaluate_stress_scenario_matrix(payload)
        self.assertEqual(func_result["evaluation_id"], evaluation_id)
        self.assertEqual(func_result["portfolio_id"], portfolio_id)
        self.assertIn("matrix_score", func_result)

if __name__ == "__main__":
    unittest.main()