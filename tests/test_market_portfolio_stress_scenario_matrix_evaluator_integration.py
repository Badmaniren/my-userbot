import unittest
import uuid
import random
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class RealDatabaseStub:
    def fetch_history(self, portfolio_id: str, historical_window: int):
        return [{"value": random.uniform(100.0, 5000.0)} for _ in range(historical_window)]

    def fetch_stream(self, portfolio_id: str):
        import io
        return io.BytesIO(b"<html><body><h1>Stress Stream Data</h1></body></html>")

class RealExtractorStub:
    def analyze(self, token: str):
        return {"anomaly_metric": random.uniform(0.0, 1.0)}

class TestMarketPortfolioStressScenarioMatrixEvaluatorIntegration(unittest.TestCase):
    def test_integration_evaluate_matrix_and_payload(self):
        db = RealDatabaseStub()
        ext1 = RealExtractorStub()
        ext2 = RealExtractorStub()
        
        evaluator = MarketPortfolioStressScenarioMatrixEvaluator(db, ext1, ext2)
        
        portfolio_id = str(uuid.uuid4())
        historical_window = random.randint(1, 10)
        
        result = evaluator.evaluate_matrix(portfolio_id, historical_window)
        
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("evaluation_score", result)
        self.assertIsInstance(result["evaluation_score"], float)
        self.assertIn("payload_data", result)

    def test_integration_stream_and_anomaly_detection(self):
        db = RealDatabaseStub()
        ext1 = RealExtractorStub()
        ext2 = RealExtractorStub()
        
        evaluator = MarketPortfolioStressScenarioMatrixEvaluator(db, ext1, ext2)
        
        portfolio_id = str(uuid.uuid4())
        stream_result = evaluator.evaluate_stream_matrix(portfolio_id, None)
        self.assertTrue(stream_result.get("fallback_triggered"))
        
        token = str(uuid.uuid4())
        threshold = random.uniform(0.1, 0.9)
        anomaly_detected = evaluator.detect_matrix_anomalies(token, threshold)
        self.assertIsInstance(anomaly_detected, bool)

    def test_integration_evaluate_stress_scenario_matrix_function(self):
        portfolio_id = str(uuid.uuid4())
        evaluation_id = str(uuid.uuid4())
        score_val = random.uniform(0.1, 0.9)
        
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {
                "score": score_val
            }
        }
        
        res = evaluate_stress_scenario_matrix(payload)
        
        self.assertEqual(res.get("evaluation_id"), evaluation_id)
        self.assertEqual(res.get("portfolio_id"), portfolio_id)
        self.assertIn("matrix_score", res)
        self.assertIsInstance(res.get("matrix_score"), float)

if __name__ == "__main__":
    unittest.main()