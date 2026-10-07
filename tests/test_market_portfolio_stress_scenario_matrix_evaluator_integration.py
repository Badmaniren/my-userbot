import unittest
import uuid
import random
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class DummyDbStorage:
    def __init__(self, history_data=None):
        self.history_data = history_data or [{"value": random.uniform(100.0, 5000.0)} for _ in range(5)]
    def fetch_history(self, portfolio_id: str, historical_window: int):
        return self.history_data
    def fetch_stream(self, portfolio_id: str):
        from io import BytesIO
        return BytesIO(b"<html><body><h1>Stress Stream Data</h1></body></html>")

class DummyExtractorTool:
    def analyze(self, scenario_token: str):
        return {"anomaly_metric": random.uniform(0.0, 1.0)}

class TestMarketPortfolioStressScenarioMatrixEvaluatorIntegration(unittest.TestCase):
    def test_end_to_end_matrix_evaluation(self):
        portfolio_id = str(uuid.uuid4())
        historical_window = random.randint(10, 100)

        db_storage = DummyDbStorage()
        extractor = DummyExtractorTool()

        evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor
        )

        matrix_result = evaluator.evaluate_matrix(portfolio_id, historical_window)

        self.assertIsInstance(matrix_result, dict)
        self.assertEqual(matrix_result.get("portfolio_id"), portfolio_id)
        self.assertIn("evaluation_score", matrix_result)
        self.assertIsInstance(matrix_result.get("evaluation_score"), float)

        stream_result = evaluator.evaluate_stream_matrix(portfolio_id, None)
        self.assertIsInstance(stream_result, dict)
        self.assertEqual(stream_result.get("portfolio_id"), portfolio_id)
        self.assertTrue(stream_result.get("fallback_triggered"))

        scenario_token = str(uuid.uuid4())
        threshold = random.uniform(0.1, 0.9)
        anomaly_detected = evaluator.detect_matrix_anomalies(scenario_token, threshold)
        self.assertIsInstance(anomaly_detected, bool)

        evaluation_id = str(uuid.uuid4())
        base_score = random.uniform(0.1, 0.9)
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {
                "score": base_score
            }
        }
        
        func_result = evaluate_stress_scenario_matrix(payload)
        self.assertIsInstance(func_result, dict)
        self.assertEqual(func_result.get("evaluation_id"), evaluation_id)
        self.assertEqual(func_result.get("portfolio_id"), portfolio_id)
        self.assertAlmostEqual(func_result.get("matrix_score"), round(base_score * 1.1, 4))

if __name__ == "__main__":
    unittest.main()